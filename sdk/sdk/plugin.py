# -*- coding: utf-8 -*-

from distutils.core import Command, run_setup
from distutils.errors import DistutilsSetupError
from pip.commands.download import DownloadCommand
from pip.utils.build import BuildDirectory
import logging, os, pkg_resources, sys, zipfile, yaml
import gnupg

class chdir():
	def __init__(self, newDir):
		self.newDir = newDir

	def __enter__(self):
		self.oldDir = os.getcwd()
		os.chdir(self.newDir)

	def __exit__(self, exc, value, tb):
		os.chdir(self.oldDir)

class telldus_plugin(Command):
	description = 'package a telldus plugin for distribution'

	user_options = [
		('dest-dir=', 'd', "Where to put the final plugin file"),
		('key-id=', 'k', "The key to sign the plugin with"),
		('prebuilt-packages-dir=', None, "Directory where prebuilt packages can be found. Egg in this dir will not be repackages by this command"),
		('skip-public-key', None, "Do not include public key in plugin. Only use this option if you know the target already have the public key"),
		('skip-dependencies=', None, "Skip including a dependency. Supply several by separating them with comma"),
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
			self.dest_dir = os.getcwd()
		if self.key_id is None:
			self.key_id = '%s <%s>' % (self.distribution.metadata.author, self.distribution.metadata.author_email)
		if type(self.skip_dependencies) == str:
			self.skip_dependencies = self.skip_dependencies.split(',')

	def run(self):
		# Get dir for output of files
		self.packageDir = '%s/package' % os.getcwd()
		self.name = self.distribution.metadata.name.replace(' ', '_')
		files = []
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
		for d in self.distribution.dist_files:
			packages.append(d[2])

		files.extend(packages)

		# Write manifest.yml
		manifest = self.__writeManifest(packages)
		files.append(manifest)

		# Sign egg files
		signatures = self.__signEggs(packages)
		files.extend(signatures)

		# Export the public key
		if not self.skip_public_key:
			key = self.__exportPublicKey()
			files.append(key)

		# Add icon
		if self.distribution.icon is not None and os.path.exists(self.distribution.icon):
			files.append(self.distribution.icon)

		# Build the final plugin as a zip-file
		self.__buildPackage(files)

	@staticmethod
	def validate_attribute(dist, attr, value):
		if attr == 'category':
			if type(value) != str:
				raise DistutilsSetupError('Attribute "category" must be a string')
		if attr == 'color':
			if type(value) != str:
				raise DistutilsSetupError('Attribute "color" must be a string')
		if attr == 'compatible_platforms':
			if type(value) != list:
				raise DistutilsSetupError('Attribute "compatible_platforms" must be a list')
		if attr == 'required_features':
			if type(value) != list:
				raise DistutilsSetupError('Attribute "required_features" must be a list')
		if attr == 'icon':
			if not os.path.exists(value):
				raise DistutilsSetupError('File %s does not exists' % value)
	
	def __buildPackage(self, files):
		if not os.path.exists(self.dest_dir):
			os.makedirs(self.dest_dir)
		with zipfile.ZipFile('%s/%s-%s.zip' % (self.dest_dir, self.name, self.distribution.metadata.version), 'w') as plugin:
			for f in files:
				plugin.write(f, os.path.basename(f))

	def __downloadRequirements(self, prebuiltPackages):
		packages = []
		with BuildDirectory(None, False) as tempDir:
			cmd = DownloadCommand()
			options, args = cmd.parse_args(['--no-binary', ':all:', '--no-clean', '-b', tempDir, '--dest', tempDir, '-r', 'requirements.txt'])
			requirement_set = cmd.run(options, args)
			for req in requirement_set.successfully_downloaded:
				dist = None
				if req.req.name in prebuiltPackages:
					packages.insert(0, prebuiltPackages[req.req.name].location)
					continue
				if req.req.name in self.skip_dependencies:
					logging.info("Do not include dependency %s", req.req.name)
					continue
				with chdir(req.source_dir):
					# Save sys.path
					sysPath = sys.path[:]
					sys.path.append(req.source_dir)
					dist = run_setup('setup.py', ['bdist_egg', '--exclude-source-files', '--dist-dir', self.packageDir])
					# Restore
					sys.path = sysPath
				if len(dist.dist_files) == 0:
					raise Exception('Requirement %s does not provide any distribution files' % req.req.name)
				for d in dist.dist_files:
					packages.insert(0, d[2])
		return packages

	def __exportPublicKey(self):
		keyfile = '%s/key.pub' % self.packageDir
		gpg = gnupg.GPG()
		key = gpg.export_keys(self.key_id)
		with open(keyfile, 'w') as f:
			f.write(key)
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
				if signature.valid == True:
					logging.warning("Signaure valid for %s, skip signing", egg)
					continue
			signature = gpg.sign_file(open(egg, "rb"), keyid=self.key_id, output=sigFile, detach=True)
			if not signature:
				raise DistutilsSetupError('Signing of %s failed: %s' % (egg, signature.stderr))
		return signatures

	def __writeManifest(self, packages):
		manifest = '%s/manifest.yml' % self.packageDir
		with open(manifest, 'w') as f:
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
			yaml.dump(data, f, default_flow_style=False)
		return manifest
