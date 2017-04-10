# -*- coding: utf-8 -*-

from base import Application, Plugin, mainthread, ConfigurationManager
from board import Board
from web.base import Server
from PluginParser import PluginParser
import glob
import gnupg
import logging
import os
import pkg_resources
import shutil
import sys
import threading
import time
import traceback
import urllib, urllib2
import yaml
import zipfile

def loadGPG():
	return gnupg.GPG(keyring='%s/plugins.keyring' % Board.pluginPath())

class LoadedPlugin(object):
	def __init__(self, manifest, context):
		self.loaded = False
		self.context = context
		self.verified = False
		self.manifest = yaml.load(open(manifest, 'r').read())
		self.name = self.manifest['name']
		self.icon = self.manifest.get('icon', '')
		self.path = os.path.dirname(manifest)
		self.packages = self.manifest['packages'] if 'packages' in self.manifest else []
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
			'author': self.manifest.get('author', ''),
			'author-email': self.manifest.get('author-email', ''),
			'category': self.manifest.get('category', 'other'),
			'color': self.manifest.get('color', ''),
			'config': configs,
			'description': self.manifest.get('description', ''),
			'icon': '/pluginloader/icon?%s' % urllib.urlencode({'name': self.name}) if self.icon != '' else '',
			'loaded': self.loaded,
			'name': self.name,
			'size': self.size(),
			'version': self.manifest.get('version', ''),
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

	def size(self):
		size = 0
		for f in os.listdir(self.path):
			size += os.path.getsize(os.path.join(self.path, f))
		return size

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
		Application().registerScheduledTask(self.updatePluginsList, days=7)
		if os.path.exists('%s/plugins.yml' % Board.pluginPath()) == False:
			# Run now
			self.updatePluginsList()
		elif time.time() - os.path.getmtime('%s/plugins.yml' % Board.pluginPath()) >= 604800:
			# The file is over 7 days old. Refresh
			self.updatePluginsList()

	def importPlugin(self, filename):
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
			try:
				gpg = loadGPG()
			except Exception as e:
				raise ImportError(str(e))
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
					#return {'success': False, 'key': self.importKey(None)}
					pass #  Do not allow importing of custom keys yet.
				raise ImportError('Could not verify plugin. Please make sure this plugin was downloaded from a trusted source.')
			path = '%s/%s' % (Board.pluginPath(), cfg['name'])
			if os.path.exists(path):
				# Wipe any old plugin
				shutil.rmtree(path)
			os.mkdir(path)
			for p, s in packages:
				shutil.move(p, '%s/%s' % (path, os.path.basename(p)))
				z.extract(s, path)
			manifest = z.extract(info, path)
			if 'icon' in cfg:
				z.extract(cfg['icon'], path)
		except zipfile.BadZipfile:
			raise ImportError('Uploaded file was not a Zip file')
		finally:
			if z is not None:
				z.close()
		os.unlink(filename)
		self.loadPlugin(manifest)
		return {'success': True, 'msg': 'Plugin was imported'}

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

	def installRemotePlugin(self, name, url, size, sha1):
		# Install in a separate thread since calls are blocking
		filename = '%s/staging.zip' % Board.pluginPath()
		server = Server(self.context)
		def downloadFile():
			u = urllib2.urlopen(url)
			meta = u.info()
			fileSize = int(meta.getheaders("Content-Length")[0])
			if size is not None and fileSize != size:
				raise Exception("Size mismatch")
				return False
			f = open(filename, 'wb')
			fileSizeDl = 0
			blockSz = 8192
			server.webSocketSend('plugins', 'downloadProgress', {'downloaded': fileSizeDl, 'size': fileSize})
			while True:
				buffer = u.read(blockSz)
				if not buffer:
						break
				fileSizeDl += len(buffer)
				f.write(buffer)
				server.webSocketSend('plugins', 'downloadProgress', {'downloaded': fileSizeDl, 'size': fileSize})
			f.close()
			return True
		def install():
			logging.warning('Install plugin %s from %s', name, url)
			try:
				downloadFile()
			except Exception as e:
				server.webSocketSend('plugins', 'downloadFailed', {'msg': str(e)})
				return
			try:
				msg = self.importPlugin(filename)
				server.webSocketSend('plugins', 'install', msg)
			except ImportError as e:
				os.unlink(filename)
				server.webSocketSend('plugins', 'install', {'success': False, 'msg':'Error importing plugin: %s' % e})
		t = threading.Thread(name='Plugin installer', target=install)
		t.daemon = True  # Kill if needed
		t.start()

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

	def updatePluginsList(self):
		# Run in a separate thread to allow blocking calls
		t = threading.Thread(target=self.__updatePluginsList, name='PluginList updater')
		t.daemon = True
		t.start()

	def __updatePluginsList(self):
		parser = PluginParser()
		data = parser.parse()
		with open('%s/plugins.yml' % Board.pluginPath(), 'w') as f:
			yaml.dump(data, f, default_flow_style=False)
		# Notify clients through websocket
		Server(self.context).webSocketSend('plugins', 'storePluginsUpdated', None)
