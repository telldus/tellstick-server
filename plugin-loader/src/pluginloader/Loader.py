# -*- coding: utf-8 -*-

from base import Plugin, mainthread, ConfigurationManager
from board import Board
from web.base import Server
import glob
import gnupg
import logging
import os
import pkg_resources
import shutil
import sys
import traceback
import yaml

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
		# Push new info to web
		Server(self.context).webSocketSend('plugins', 'pluginInfo', self.infoObject())

	def __loadEgg(self, egg):
		for dist in pkg_resources.find_distributions('%s/%s' % (self.path, egg)):
			logging.warning("Loading plugin %s %s", dist.project_name, dist.version)
			dist.activate()
			for entry in dist.get_entry_map(group='telldus.plugins'):
				info = dist.get_entry_info('telldus.plugins', entry)
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


