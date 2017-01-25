# -*- coding: utf-8 -*-

from base import Plugin, implements #, mainthread, ConfigurationManager
from board import Board
from web.base import IWebRequestHandler, WebResponseJson
from telldus import IWebReactHandler
from Loader import Loader
import gnupg
import json
import os
import shutil
import yaml
import zipfile

def loadGPG():
	return gnupg.GPG(keyring='%s/plugins.keyring' % Board.pluginPath())

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
		return {'success': False, 'msg': 'Importing of custom keys are not allowed'}
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
