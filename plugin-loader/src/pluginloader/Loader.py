# -*- coding: utf-8 -*-

from base import Plugin, implements
from board import Board
from web.base import IWebRequestHandler, WebResponseRedirect
import glob
import gnupg
import logging
import os
import pkg_resources
import shutil
import traceback
import yaml
import zipfile

def loadGPG():
	return gnupg.GPG(keyring='%s/plugins.keyring' % Board.pluginPath())

class LoadedPlugin(object):
	def __init__(self, manifest, context):
		self.loaded = False
		self.context = context
		self.verified = False
		cfg = yaml.load(open(manifest, 'r').read())
		self.name = cfg['name']
		self.path = os.path.dirname(manifest)
		self.packages = cfg['packages'] if 'packages' in cfg else []

	def printBacktrace(self, bt):
		for f in bt:
			logging.error(str(f))

	def remove(self):
		shutil.rmtree(self.path)

	def verify(self):
		for p in self.packages:
			if not LoadedPlugin.__verifyFile('%s/%s' % (self.path, p)):
				return False
		return True

	def verifyAndLoad(self):
		try:
			if not self.verify():
				return
		except Exception as e:
			logging.warning("Could not load plugin %s: %s", self.name, str(e))
			return
		for p in self.packages:
			self.__loadEgg(p)
		self.loaded = True

	def __loadEgg(self, egg):
		for dist in pkg_resources.find_distributions('%s/%s' % (self.path, egg)):
			logging.warning("Loading plugin %s %s", dist.project_name, dist.version)
			dist.activate()
			for entry in dist.get_entry_map(group='telldus.plugins'):
				info = dist.get_entry_info('telldus.startup', entry)
				try:
					info.load()
				except Exception as e:
					exc_type, exc_value, exc_traceback = sys.exc_info()
					logging.error("Could not load %s", str(entry))
					logging.error(str(e))
					self.printBacktrace(traceback.extract_tb(exc_traceback))

			for entry in dist.get_entry_map(group='telldus.startup'):
				info = dist.get_entry_info('telldus.startup', entry)
				try:
					moduleClass = info.load()
					if issubclass(moduleClass, Plugin):
						m = moduleClass(self.context)
					else:
						m = moduleClass()
				except Exception as e:
					exc_type, exc_value, exc_traceback = sys.exc_info()
					logging.error("Could not load %s", str(entry))
					logging.error(str(e))
					self.printBacktrace(traceback.extract_tb(exc_traceback))

	@staticmethod
	def __verifyFile(path):
		# Check signature
		gpg = loadGPG()
		v = gpg.verify_file(open('%s.asc' % path, 'rb'), path)
		if v.valid is not True:
			raise Exception('Could not verify signature: %s' % v.status)
		return True

class Loader(Plugin):
	def __init__(self):
		self.plugins = []
		self.initializeKeychain()
		self.loadPlugins()

	def initializeKeychain(self):
		filename = pkg_resources.resource_filename('pluginloader', 'files/telldus.gpg')
		gpg = loadGPG()
		installedKeys = [key['keyid'] for key in gpg.list_keys()]
		defaultKeys = gpg.scan_keys(filename)
		for key in [key['keyid'] for key in defaultKeys]:
			if key in installedKeys:
				continue
			gpg.import_keys(open(filename, 'rb').read())
			return

	def loadPlugin(self, manifest):
		plugin = LoadedPlugin(manifest, self.context)
		plugin.verifyAndLoad()
		self.plugins.append(plugin)

	def loadPlugins(self):
		for f in glob.glob('%s/**/manifest.yml' % Board.pluginPath()):
			self.loadPlugin(f)

	def removePlugin(self, name):
		for i, plugin in enumerate(self.plugins):
			if plugin.name != name:
				continue
			plugin.remove()
			del self.plugins[i]
			return

class WebFrontend(Plugin):
	implements(IWebRequestHandler)

	def importKey(self, acceptKeyId):
		filename = '%s/staging.zip' % Board.pluginPath()
		if not os.path.exists(filename):
			return WebResponseRedirect('/')
		try:
			gpg = loadGPG()
			with zipfile.ZipFile(filename, 'r') as z:
				cfg = yaml.load(z.read('manifest.yml'))
				k = z.extract(cfg['key'], '/tmp/')
				keys = gpg.scan_keys(k)
				if len(keys) != 1:
					raise Exception('Key must only contain exactly one public key')
				key = keys[0]
				name = key['uids']
				fingerprint = key['fingerprint']
				keyid = key['keyid']
				if keyid != acceptKeyId:
					return 'importkey.html', {'name': name, 'fingerprint': fingerprint, 'keyid': keyid}
				result = gpg.import_keys(open(k).read())
				os.unlink(k)
		except Exception as e:
			os.unlink(filename)
			return 'pluginloader.html', {'msg': str(e), 'loader': Loader(self.context)}
		return WebResponseRedirect('/')

	def importPlugin(self):
		filename = '%s/staging.zip' % Board.pluginPath()
		with zipfile.ZipFile(filename, 'r') as z:
			try:
				info = z.getinfo('manifest.yml')
			except KeyError:
				raise ImportError('Malformed plugin. No manifest found.')
			cfg = yaml.load(z.read('manifest.yml'))
			if 'name' not in cfg:
				raise ImportError('Malformed plugin. Plugin has no name.')
			if cfg['name'] == 'staging':
				raise ImportError('Plugin name cannot be "staging", this is a reserved name')
			if 'packages' not in cfg:
				raise ImportError('Malformed plugin. Manifest does not list any packages.')
			gpg = loadGPG()
			packages = []
			for p in cfg['packages']:
				f = z.extract(p, '/tmp/')
				s = z.getinfo('%s.asc' % p)
				packages.append((f, s,))
				result = gpg.verify_file(z.open(s), f)
				if result.valid is True:
					continue
				# remove unpackaged files
				for p, s in packages:
					os.unlink(p)
				if result.pubkey_fingerprint is None and result.username is None:
					# No public key for this plugin
					return WebResponseRedirect('/importkey')
				raise ImportError('Could not verify plugin')
			path = '%s/%s' % (Board.pluginPath(), cfg['name'])
			if os.path.exists(path):
				# Wipe any old plugin
				shutil.rmtree(path)
			os.mkdir(path)
			for p, s in packages:
				os.rename(p, '%s/%s' % (path, os.path.basename(p)))
				z.extract(s, path)
			manifest = z.extract(info, path)
		os.unlink(filename)
		loader = Loader(self.context)
		loader.loadPlugin(manifest)
		return 'pluginloader.html', {'msg': 'Plugin was imported', 'loader': loader}

	def uploadPlugin(self, f):
		with open('%s/staging.zip' % (Board.pluginPath()), 'w') as wf:
			wf.write(f.file.read())

	def getTemplatesDirs(self):
		return [pkg_resources.resource_filename('pluginloader', 'templates')]

	def matchRequest(self, plugin, path):
		if plugin != 'pluginloader':
			return False
		if path in ['', 'importkey', 'remove']:
			return True
		return False

	def handleRequest(self, plugin, path, params, request, **kwargs):
		if request.method() == 'POST' and 'pluginfile' in params:
			self.uploadPlugin(params['pluginfile'])
			return WebResponseRedirect('/')

		if path == 'importkey':
			if 'discard' in params:
				os.unlink('%s/staging.zip' % (Board.pluginPath()))
				return WebResponseRedirect('/')
			return self.importKey(params['key'] if 'key' in params else None)

		if path == 'remove':
			if 'pluginname' in params:
				Loader(self.context).removePlugin(params['pluginname'])
			return WebResponseRedirect('/')

		if os.path.isfile('%s/staging.zip' % (Board.pluginPath())):
			try:
				return self.importPlugin()
			except ImportError as e:
				os.unlink('%s/staging.zip' % (Board.pluginPath()))
				return 'pluginloader.html', {'msg':'Error importing plugin: %s' % e, 'loader': Loader(self.context)}
		return 'pluginloader.html', {'msg':'', 'loader': Loader(self.context)}
