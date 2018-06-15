# -*- coding: utf-8 -*-

import glob
import logging
import os
import shutil
import sys
import threading
import time
import traceback
import urllib2
import zipfile
import pkg_resources
import gnupg

from six.moves.urllib.parse import urlencode
import yaml

from base import Application, Plugin, mainthread, ConfigurationManager
from board import Board
from web.base import Server

from .PluginParser import PluginParser

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

	def configuration(self, pluginClass, configurationName):
		configuration = ConfigurationManager(self.context)
		for cls in self.classes:
			name = '%s.%s' % (cls.__module__, cls.__name__)
			if pluginClass != name:
				continue
			return configuration.configObject(name, configurationName)

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
			'long_description': self.manifest.get('long_description', ''),
			'description': self.manifest.get('description', ''),
			'icon': '/pluginloader/icon?%s' %
				urlencode({'name': self.name}) if self.icon != '' else '',
			'loaded': self.loaded,
			'name': self.name,
			'size': self.size(),
			'version': self.manifest.get('version', ''),
		}

	@staticmethod
	def printBacktrace(backtrace):
		for func in backtrace:
			logging.error(str(func))

	def remove(self):
		for cls in self.classes:
			plugin = self.context.components.get(cls)
			if not plugin:
				continue
			if not hasattr(plugin, 'tearDown'):
				continue
			try:
				plugin.tearDown()
			except Exception as error:
				Application.printException(error)
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
		for filename in os.listdir(self.path):
			size += os.path.getsize(os.path.join(self.path, filename))
		return size

	def verify(self):
		for package in self.packages:
			if not LoadedPlugin.__verifyFile('%s/%s' % (self.path, package)):
				return False
		return True

	@mainthread
	def verifyAndLoad(self):
		try:
			if not self.verify():
				return
		except Exception as exception:
			logging.warning("Could not load plugin %s: %s", self.name, str(exception))
			return
		for package in self.packages:
			self.__loadEgg(package)
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
				except Exception as exception:
					_exc_type, _exc_value, exc_traceback = sys.exc_info()
					logging.error("Could not load %s", str(entry))
					logging.error(str(exception))
					self.printBacktrace(traceback.extract_tb(exc_traceback))

			for entry in dist.get_entry_map(group='telldus.startup'):
				info = dist.get_entry_info('telldus.startup', entry)
				try:
					moduleClass = info.load()
					self.classes.append(moduleClass)
					if issubclass(moduleClass, Plugin):
						moduleClass(self.context)
					else:
						moduleClass()
				except Exception as exception:
					_exc_type, _exc_value, exc_traceback = sys.exc_info()
					logging.error("Could not load %s", str(entry))
					logging.error(str(exception))
					self.printBacktrace(traceback.extract_tb(exc_traceback))

	@staticmethod
	def __verifyFile(path):
		# Check signature
		gpg = loadGPG()
		result = gpg.verify_file(open('%s.asc' % path, 'rb'), path)
		if result.valid is not True:
			raise Exception('Could not verify signature: %s' % result.status)
		return True

class Loader(Plugin):
	def __init__(self, *args):
		del args
		self.plugins = []
		self.initializeKeychain()
		self.loadPlugins()
		Application().registerScheduledTask(self.updatePluginsList, days=7)
		if not os.path.exists('%s/plugins.yml' % Board.pluginPath()):
			# Run now
			self.updatePluginsList()
		elif time.time() - os.path.getmtime('%s/plugins.yml' % Board.pluginPath()) >= 604800:
			# The file is over 7 days old. Refresh
			self.updatePluginsList()

	def configurationForPlugin(self, pluginName, pluginClass, configuration):
		for plugin in self.plugins:
			if plugin.name != pluginName:
				continue
			return plugin.configuration(pluginClass, configuration)
		return None

	def importKey(self, acceptKeyId):
		# return {'success': False, 'msg': 'Importing of custom keys are not allowed'}
		filename = '%s/staging.zip' % Board.pluginPath()
		if not os.path.exists(filename):
			return {'success': False, 'msg': 'No plugin uploaded'}
		try:
			gpg = loadGPG()
			with zipfile.ZipFile(filename, 'r') as zipF:
				cfg = yaml.load(zipF.read('manifest.yml'))
				keyFile = zipF.extract(cfg['key'], '/tmp/')
				keys = gpg.scan_keys(keyFile)
				if len(keys) != 1:
					raise Exception('Key must only contain exactly one public key')
				key = keys[0]
				name = key['uids']
				fingerprint = key['fingerprint']
				keyid = key['keyid']
				if keyid != acceptKeyId:
					return {'name': name, 'fingerprint': fingerprint, 'keyid': keyid}
				gpg.import_keys(open(keyFile).read())
				os.unlink(keyFile)
				# Reload loaded keys
				# pylint: disable=too-many-function-args
				Loader(self.context).initializeKeychain()
		except Exception as exception:
			os.unlink(filename)
			return "multiKeyError", {'success': False, 'msg': str(exception)}
		return {'success': True}

	def importPlugin(self, filename):
		zipF = None
		try:
			zipF = zipfile.ZipFile(filename, 'r')
			try:
				info = zipF.getinfo('manifest.yml')
			except KeyError:
				raise ImportError('Malformed plugin. No manifest found.')
			cfg = yaml.load(zipF.read('manifest.yml'))
			if 'name' not in cfg:
				raise ImportError('Malformed plugin. Plugin has no name.')
			if cfg['name'] == 'staging':
				raise ImportError('Plugin name cannot be "staging", this is a reserved name')
			if 'packages' not in cfg:
				raise ImportError('Malformed plugin. Manifest does not list any packages.')
			try:
				gpg = loadGPG()
			except OSError as error:
				raise ImportError(str(error))
			packages = []
			for package in cfg['packages']:
				packageFilename = zipF.extract(package, '/tmp/')
				signature = zipF.getinfo('%s.asc' % package)
				packages.append((packageFilename, signature,))
				result = gpg.verify_file(zipF.open(signature), packageFilename)
				if result.valid is True:
					continue
				# remove unpackaged files
				for packageFilename, _signature in packages:
					os.unlink(packageFilename)
				if result.pubkey_fingerprint is None and result.username is None:
					# No public key for this plugin
					keyStatus = self.importKey(None)
					if isinstance(keyStatus, tuple):
						return keyStatus[1]
					else:
						return {'success': False, 'key': keyStatus[1]}
				raise ImportError(
					'Could not verify plugin. Please make sure this plugin was downloaded from a trusted source.'
				)
			path = '%s/%s' % (Board.pluginPath(), cfg['name'])
			if os.path.exists(path):
				# Wipe any old plugin
				shutil.rmtree(path)
			os.mkdir(path)
			for packageFilename, signature in packages:
				shutil.move(packageFilename, '%s/%s' % (path, os.path.basename(packageFilename)))
				zipF.extract(signature, path)
			manifest = zipF.extract(info, path)
			if 'icon' in cfg:
				zipF.extract(cfg['icon'], path)
		except zipfile.BadZipfile:
			raise ImportError('Uploaded file was not a Zip file')
		finally:
			if zipF is not None:
				zipF.close()
		os.unlink(filename)
		status = self.loadPlugin(manifest)
		return {
			'success': True,
			'msg': 'Plugin was imported',
			'restartRequired': True if status == 1 else False
		}

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
		del sha1
		# Install in a separate thread since calls are blocking
		filename = '%s/staging.zip' % Board.pluginPath()
		server = Server(self.context)
		def downloadFile():
			urlFd = urllib2.urlopen(url)
			meta = urlFd.info()
			fileSize = int(meta.getheaders("Content-Length")[0])
			if size is not None and fileSize != size:
				raise Exception("Size mismatch")
			fd = open(filename, 'wb')
			fileSizeDl = 0
			blockSz = 8192
			server.webSocketSend('plugins', 'downloadProgress', {'downloaded': fileSizeDl, 'size': fileSize})
			while True:
				buff = urlFd.read(blockSz)
				if not buff:
					break
				fileSizeDl += len(buff)
				fd.write(buff)
				server.webSocketSend(
					'plugins',
					'downloadProgress',
					{'downloaded': fileSizeDl, 'size': fileSize}
				)
			fd.close()
			return True
		def install():
			logging.warning('Install plugin %s from %s', name, url)
			try:
				downloadFile()
			except Exception as exception:
				server.webSocketSend('plugins', 'downloadFailed', {'msg': str(exception)})
				return
			try:
				msg = self.importPlugin(filename)
				server.webSocketSend('plugins', 'install', msg)
			except ImportError as error:
				os.unlink(filename)
				server.webSocketSend(
					'plugins',
					'install',
					{'success': False, 'msg':'Error importing plugin: %s' % error}
				)
		thread = threading.Thread(name='Plugin installer', target=install)
		thread.daemon = True  # Kill if needed
		thread.start()

	def loadPlugin(self, manifest):
		plugin = LoadedPlugin(manifest, self.context)
		plugin.verifyAndLoad()
		for i, loadedPlugin in enumerate(self.plugins):
			if loadedPlugin.name == plugin.name:
				self.plugins[i] = plugin
				return 1
		self.plugins.append(plugin)
		return 0

	def loadPlugins(self):
		for filename in glob.glob('%s/**/manifest.yml' % Board.pluginPath()):
			self.loadPlugin(filename)

	def removeKey(self, __key, fingerprint):
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
		thread = threading.Thread(target=self.__updatePluginsList, name='PluginList updater')
		thread.daemon = True
		thread.start()

	def __updatePluginsList(self):
		parser = PluginParser()
		data = parser.parse()
		with open('%s/plugins.yml' % Board.pluginPath(), 'w') as fd:
			yaml.dump(data, fd, default_flow_style=False)
		# Notify clients through websocket
		Server(self.context).webSocketSend('plugins', 'storePluginsUpdated', None)
