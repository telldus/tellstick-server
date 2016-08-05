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

class Loader(Plugin):
	def __init__(self):
		self.loadPlugins()

	def loadPlugins(self):
		for f in glob.glob('%s/**/manifest.yml' % Board.pluginPath()):
			try:
				self.verifyAndLoadPlugin(f)
			except Exception as e:
				logging.error('Could not load plugin: %s', e)

	def printBacktrace(self, bt):
		for f in bt:
			logging.error(str(f))

	def verifyAndLoadPlugin(self, path):
		cfg = yaml.load(open(path, 'r').read())
		if 'packages' not in cfg:
			return
		d = os.path.dirname(path)
		for p in cfg['packages']:
			if not self.verifyPlugin('%s/%s' % (d, p)):
				return
		for p in cfg['packages']:
			self.__loadPlugin('%s/%s' % (d, p))

	def verifyPlugin(self, path):
		# Check signature
		gpg = loadGPG()
		v = gpg.verify_file(open('%s.asc' % path, 'rb'), path)
		if v.valid is not True:
			raise Exception('Could not verify signature: %s' % v.status)
		return True

	def __loadPlugin(self, path):
		for dist in pkg_resources.find_distributions(path):
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
			return 'pluginloader.html', {'msg': str(e)}
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
			z.extract(info, path)
		os.unlink(filename)
		return 'pluginloader.html', {'msg': 'Plugin was imported'}

	def uploadPlugin(self, f):
		with open('%s/staging.zip' % (Board.pluginPath()), 'w') as wf:
			wf.write(f.file.read())

	def getTemplatesDirs(self):
		return [pkg_resources.resource_filename('pluginloader', 'templates')]

	def matchRequest(self, plugin, path):
		if plugin != 'pluginloader':
			return False
		if path in ['', 'importkey']:
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
		if os.path.isfile('%s/staging.zip' % (Board.pluginPath())):
			try:
				return self.importPlugin()
			except ImportError as e:
				os.unlink('%s/staging.zip' % (Board.pluginPath()))
				return 'pluginloader.html', {'msg':'Error importing plugin: %s' % e}
		return 'pluginloader.html', {'msg':''}
