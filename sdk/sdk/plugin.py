# -*- coding: utf-8 -*-

import os
import sys
import zipfile
from distutils.core import Command, run_setup
from distutils.errors import DistutilsSetupError
from distutils.log import info, warn

import pkg_resources
import yaml
import gnupg
from pip._internal.commands.download import DownloadCommand  # pylint: disable=E0611
from pip._internal.utils.temp_dir import TempDirectory  # pylint: disable=E0611

class chdir(object):  # pylint: disable=C0103
	def __init__(self, newDir):
		self.newDir = newDir
		self.oldDir = None

	def __enter__(self):
		self.oldDir = os.getcwd()
		os.chdir(self.newDir)

	def __exit__(self, exc, value, __tb):
		os.chdir(self.oldDir)

class telldus_plugin(Command):  # pylint: disable=C0103
	# These are common dependencies used by plugins already available in the firmware.
	# Skip including these
	builtins = [
		'netifaces',
		'requests',
		'six',
	]
	description = 'package a telldus plugin for distribution'

	user_options = [
		('dest-dir=', 'd', "Where to put the final plugin file"),
		('key-id=', 'k', "The key to sign the plugin with"),
		('prebuilt-packages-dir=', None,
			"Directory where prebuilt packages can be found. Egg \
			in this dir will not be repackages by this command"),
		('skip-public-key', None,
			"Do not include public key in plugin. Only use this \
			option if you know the target already have the public key"),
		('skip-dependencies=', None,
			"Skip including a dependency. Supply several by \
			separating them with comma"),
	]

	boolean_options = [
		'skip-public-key'
	]

	def initialize_options(self):
		self.skip_public_key = False
		self.skip_dependencies = []
		self.prebuilt_packages_dir = None
		self.key_id = None
		self.dest_dir = None

	def finalize_options(self):
		if self.dest_dir is None:
			self.dest_dir = os.getcwd()  # pylint: disable=W0201
		if self.key_id is None:
			# pylint: disable=W0201
			self.key_id = '%s <%s>' % (
				self.distribution.metadata.author,
				self.distribution.metadata.author_email
			)
		if isinstance(self.skip_dependencies, str):
			self.skip_dependencies = self.skip_dependencies.split(',')  # pylint: disable=E1101,W0201
		self.skip_dependencies.extend(telldus_plugin.builtins)

	def run(self):
		# Get dir for output of files
		self.packageDir = '%s/package' % os.getcwd()  # pylint: disable=W0201
		self.name = self.distribution.metadata.name.replace(' ', '_')  # pylint: disable=W0201
		files = set()
		packages = []

		# Find prebuilt packages
		prebuiltPackages = {}
		if self.prebuilt_packages_dir is not None and os.path.exists(self.prebuilt_packages_dir):
			for filename in os.listdir(self.prebuilt_packages_dir):
				if not filename.endswith('.egg'):
					continue
				path = os.path.abspath(os.path.join(self.prebuilt_packages_dir, filename))
				for metadata in pkg_resources.find_distributions(path):
					prebuiltPackages[metadata.project_name] = metadata

		# Download and package dependencies for the project
		if os.path.exists('%s/requirements.txt' % os.getcwd()):
			requirements = self.__downloadRequirements(prebuiltPackages)
			packages.extend(requirements)

		# Build the plugin as egg
		cmdObj = self.distribution.get_command_obj('bdist_egg')
		cmdObj.dist_dir = self.packageDir
		cmdObj.exclude_source_files = True
		self.run_command('bdist_egg')
		for distfile in self.distribution.dist_files:
			if distfile[2] in packages:
				continue
			packages.append(distfile[2])

		files.update(packages)

		# Write manifest.yml
		manifest = self.__writeManifest(packages)
		files.add(manifest)

		# Sign egg files
		signatures = self.__signEggs(packages)
		files.update(signatures)

		# Export the public key
		if not self.skip_public_key:
			key = self.__exportPublicKey()
			files.add(key)

		# Add icon
		if self.distribution.icon is not None and os.path.exists(self.distribution.icon):
			files.add(self.distribution.icon)

		# Build the final plugin as a zip-file
		self.__buildPackage(files)

	@staticmethod
	def validate_attribute(__dist, attr, value):
		if attr == 'category':
			if not isinstance(value, str):
				raise DistutilsSetupError('Attribute "category" must be a string')
		if attr == 'color':
			if not isinstance(value, str):
				raise DistutilsSetupError('Attribute "color" must be a string')
		if attr == 'compatible_platforms':
			if not isinstance(value, list):
				raise DistutilsSetupError('Attribute "compatible_platforms" must be a list')
		if attr == 'ports':
			if not isinstance(value, dict):
				raise DistutilsSetupError('Attribute "ports" must be a dictionary')
		if attr == 'required_features':
			if not isinstance(value, list):
				raise DistutilsSetupError('Attribute "required_features" must be a list')
		if attr == 'icon':
			if not os.path.exists(value):
				raise DistutilsSetupError('File %s does not exists' % value)

	@staticmethod
	def write_metadata(cmd, basename, filename):
		what = os.path.splitext(basename)[0]
		metadata = {}
		ports = getattr(cmd.distribution, 'ports', None)
		if ports is not None:
			metadata['ports'] = ports
		cmd.write_or_delete_file(what, filename, yaml.dump(metadata))

	def __buildPackage(self, files):
		if not os.path.exists(self.dest_dir):
			os.makedirs(self.dest_dir)
		filename = '%s/%s-%s.zip' % (self.dest_dir, self.name, self.distribution.metadata.version)
		with zipfile.ZipFile(filename, 'w') as plugin:
			for filename in files:
				plugin.write(filename, os.path.basename(filename))

	def __downloadRequirements(self, prebuiltPackages):
		packages = []
		with TempDirectory(None, False) as tempDir:
			cmd = DownloadCommand()
			options, args = cmd.parse_args([
				'--no-binary',
				':all:',
				'--no-clean',
				'-b', tempDir.path,
				'--dest', tempDir.path,
				'-r', 'requirements.txt'
			])
			requirement_set = cmd.run(options, args)
			for req in requirement_set.successfully_downloaded:
				dist = None
				if req.req.name in prebuiltPackages:
					packages.insert(0, prebuiltPackages[req.req.name].location)
					continue
				if req.req.name in self.skip_dependencies:
					info("Do not include dependency %s", req.req.name)
					continue
				with chdir(req.source_dir):
					# Save sys.path
					sysPath = sys.path[:]
					sys.path.append(req.source_dir)
					dist = run_setup('setup.py', [
						'bdist_egg',
						'--exclude-source-files',
						'--dist-dir', self.packageDir
					])
					# Restore
					sys.path = sysPath
				if len(dist.dist_files) == 0:
					raise Exception('Requirement %s does not provide any distribution files' % req.req.name)
				for distfile in dist.dist_files:
					packages.insert(0, distfile[2])
		return packages

	def __exportPublicKey(self):
		keyfile = '%s/key.pub' % self.packageDir
		gpg = gnupg.GPG()
		key = gpg.export_keys(self.key_id)
		with open(keyfile, 'w') as fd:
			fd.write(key)
		return keyfile

	def __signEggs(self, eggs):
		signatures = []
		gpg = gnupg.GPG()
		for egg in eggs:
			sigFile = '%s.asc' % egg
			signatures.append(sigFile)
			if os.path.exists(sigFile):
				# Check signature to see if we should resign
				signature = gpg.verify_file(open(sigFile, 'rb'), egg)
				if signature.valid is True:
					warn("Signaure valid for %s, skip signing", egg)
					continue
			signature = gpg.sign_file(open(egg, "rb"), keyid=self.key_id, output=sigFile, detach=True)
			if not signature:
				raise DistutilsSetupError('Signing of %s failed: %s' % (egg, signature.stderr))
		return signatures

	def __writeManifest(self, packages):
		manifest = '%s/manifest.yml' % self.packageDir
		with open(manifest, 'w') as fd:
			data = {
				'description': self.distribution.metadata.description,
				'name': self.distribution.metadata.name,
				'author': self.distribution.metadata.author,
				'author-email': self.distribution.metadata.author_email,
				'package-version': 1,
				'packages': [os.path.basename(p) for p in packages],
				'version': self.distribution.metadata.version,
			}
			if self.distribution.category is not None:
				data['category'] = self.distribution.category
			if self.distribution.color is not None:
				data['color'] = self.distribution.color
			if self.distribution.icon is not None and os.path.exists(self.distribution.icon):
				data['icon'] = self.distribution.icon
			if self.distribution.metadata.long_description is not None:
				data['long_description'] = self.distribution.metadata.long_description
			if not self.skip_public_key:
				data['key'] = 'key.pub'
			if self.distribution.compatible_platforms:
				data['compatible-platforms'] = self.distribution.compatible_platforms
			if self.distribution.required_features:
				data['required-features'] = self.distribution.required_features
			yaml.dump(data, fd, default_flow_style=False)
		return manifest
