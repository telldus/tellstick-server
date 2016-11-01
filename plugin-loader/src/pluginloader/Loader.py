# -*- coding: utf-8 -*-

from base import Plugin, implements, mainthread, ConfigurationManager
from board import Board
from web.base import IWebRequestHandler, WebResponseRedirect, WebResponseJson
from telldus import IWebReactHandler
import glob
import gnupg
import json
import logging
import os
import pkg_resources
import shutil
import sys
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
		self.classes = []

	def infoObject(self):
		configuration = ConfigurationManager(self.context)
		configs = {}
		for cls in self.classes:
			cfg = configuration.configForClass(cls)
			if cfg is None:
				continue
			configs['%s.%s' % (cls.__module__, cls.__name__)] = cfg

		return {
			'name': self.name,
			'loaded': self.loaded,
			'config': configs
		}

	def printBacktrace(self, bt):
		for f in bt:
			logging.error(str(f))

	def remove(self):
		shutil.rmtree(self.path)

	def saveConfiguration(self, configs):
		configuration = ConfigurationManager(self.context)
		for cls in self.classes:
			name = '%s.%s' % (cls.__module__, cls.__name__)
			if name not in configs:
				continue
			for key in configs[name]:
				configuration.setValue(cls, key, configs[name][key])

	def verify(self):
		for p in self.packages:
			if not LoadedPlugin.__verifyFile('%s/%s' % (self.path, p)):
				return False
		return True

	@mainthread
	def verifyAndLoad(self):
		try:
			if not self.verify():
				return
		except Exception as e:
			logging.warning("Could not load plugin %s: %s", self.name, str(e))
			return
		for p in self.packages:
			self.__loadEgg(p)
		# TODO: Do not just set the loaded flag here. Make sure the eggs where loaded and store any
		# backtrace if the loading failed.
		self.loaded = True

	def __loadEgg(self, egg):
		for dist in pkg_resources.find_distributions('%s/%s' % (self.path, egg)):
			logging.warning("Loading plugin %s %s", dist.project_name, dist.version)
			dist.activate()
			for entry in dist.get_entry_map(group='telldus.plugins'):
				info = dist.get_entry_info('telldus.startup', entry)
				try:
					moduleClass = info.load()
					self.classes.append(moduleClass)
				except Exception as e:
					exc_type, exc_value, exc_traceback = sys.exc_info()
					logging.error("Could not load %s", str(entry))
					logging.error(str(e))
					self.printBacktrace(traceback.extract_tb(exc_traceback))

			for entry in dist.get_entry_map(group='telldus.startup'):
				info = dist.get_entry_info('telldus.startup', entry)
				try:
					moduleClass = info.load()
					self.classes.append(moduleClass)
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
		defaultKeys = [key['keyid'] for key in gpg.scan_keys(filename)]
		for key in defaultKeys:
			if key in installedKeys:
				continue
			gpg.import_keys(open(filename, 'rb').read())
			break
		# List all keys except builtin ones
		self.keys = [x for x in gpg.list_keys() if x['keyid'] not in defaultKeys]

	def loadPlugin(self, manifest):
		plugin = LoadedPlugin(manifest, self.context)
		plugin.verifyAndLoad()
		self.plugins.append(plugin)

	def loadPlugins(self):
		for f in glob.glob('%s/**/manifest.yml' % Board.pluginPath()):
			self.loadPlugin(f)

	def removeKey(self, key, fingerprint):
		gpg = loadGPG()
		gpg.delete_keys(fingerprint, True)
		gpg.delete_keys(fingerprint)
		# Reload keys and make sure the built in stays
		self.initializeKeychain()

	def removePlugin(self, name):
		for i, plugin in enumerate(self.plugins):
			if plugin.name != name:
				continue
			plugin.remove()
			del self.plugins[i]
			return

	def saveConfiguration(self, pluginName, configurations):
		for plugin in self.plugins:
			if plugin.name != pluginName:
				continue
			plugin.saveConfiguration(configurations)
			return {'success': True}
		raise Exception('Could not find plugin %s' % pluginName)

class WebFrontend(Plugin):
	implements(IWebRequestHandler)
	implements(IWebReactHandler)

	def getReactRoutes(self):
		return [{
			'name': 'plugins',
			'title': 'Plugins (beta)',
			'script': 'pluginloader/plugins.js'
		}]

	def importKey(self, acceptKeyId):
		filename = '%s/staging.zip' % Board.pluginPath()
		if not os.path.exists(filename):
			return {'success': False, 'msg': 'No plugin uploaded'}
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
					return {'name': name, 'fingerprint': fingerprint, 'keyid': keyid}
				result = gpg.import_keys(open(k).read())
				os.unlink(k)
				# Reload loaded keys
				Loader(self.context).initializeKeychain()
		except Exception as e:
			os.unlink(filename)
			return {'success': False, 'msg': str(e)}
		return {'success': True}

	def importPlugin(self):
		filename = '%s/staging.zip' % Board.pluginPath()
		z = None
		try:
			z = zipfile.ZipFile(filename, 'r')
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
					return {'success': False, 'key': self.importKey(None)}
				raise ImportError('Could not verify plugin')
			path = '%s/%s' % (Board.pluginPath(), cfg['name'])
			if os.path.exists(path):
				# Wipe any old plugin
				shutil.rmtree(path)
			os.mkdir(path)
			for p, s in packages:
				shutil.move(p, '%s/%s' % (path, os.path.basename(p)))
				z.extract(s, path)
			manifest = z.extract(info, path)
		except zipfile.BadZipfile:
			raise ImportError('Uploaded file was not a Zip file')
		finally:
			if z is not None:
				z.close()
		os.unlink(filename)
		loader = Loader(self.context)
		loader.loadPlugin(manifest)
		return {'success': True, 'msg': 'Plugin was imported'}

	def uploadPlugin(self, f):
		with open('%s/staging.zip' % (Board.pluginPath()), 'w') as wf:
			wf.write(f.file.read())

	def getTemplatesDirs(self):
		return [pkg_resources.resource_filename('pluginloader', 'templates')]

	def matchRequest(self, plugin, path):
		if plugin != 'pluginloader':
			return False
		if path in ['import', 'importkey', 'keys', 'remove', 'plugins', 'saveConfiguration', 'upload']:
			return True
		return False

	def handleRequest(self, plugin, path, params, request, **kwargs):
		if path == 'import':
			if os.path.isfile('%s/staging.zip' % (Board.pluginPath())):
				try:
					return WebResponseJson(self.importPlugin())
				except ImportError as e:
					os.unlink('%s/staging.zip' % (Board.pluginPath()))
					return WebResponseJson({'success': False, 'msg':'Error importing plugin: %s' % e})
			return WebResponseJson({'success': False, 'msg':'Error importing plugin: No plugin uploaded'})

		if path == 'importkey':
			if 'discard' in params:
				os.unlink('%s/staging.zip' % (Board.pluginPath()))
				return WebResponseJson({'success': True})
			return WebResponseJson(self.importKey(params['key'] if 'key' in params else None))

		if path == 'remove':
			if 'pluginname' in params:
				Loader(self.context).removePlugin(params['pluginname'])
			elif 'key' in params and 'fingerprint' in params:
				Loader(self.context).removeKey(params['key'], params['fingerprint'])
			else:
				return WebResponseJson({'success': False, 'msg': 'No plugin or key specified'})
			return WebResponseJson({'success': True})

		if path == 'plugins':
			return WebResponseJson([plugin.infoObject() for plugin in Loader(self.context).plugins])

		if path == 'keys':
			return WebResponseJson([
				{
					'uids': key['uids'],
					'keyid': key['keyid'],
					'fingerprint': key['fingerprint']
				}
				for key in Loader(self.context).keys
			])

		if path == 'saveConfiguration' and request.method() == 'POST':
			plugin = params['pluginname']
			configuration = json.loads(params['configuration'])
			try:
				Loader(self.context).saveConfiguration(plugin, configuration)
			except Exception as e:
				return WebResponseJson({'success': False, 'msg': str(e)})
			return WebResponseJson({'success': True})

		if path == 'upload' and request.method() == 'POST':
			self.uploadPlugin(params['pluginfile'])
			try:
				return WebResponseJson(self.importPlugin())
			except ImportError as e:
				os.unlink('%s/staging.zip' % (Board.pluginPath()))
				return WebResponseJson({'success': False, 'msg': str(e)})

		return 'pluginloader.html', {'msg':'', 'loader': Loader(self.context)}
