# -*- coding: utf-8 -*-

from base import Plugin, implements
from board import Board
from web.base import IWebRequestHandler, WebResponseLocalFile, WebResponseJson
from telldus.web import IWebReactHandler
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

	def getReactComponents(self):
		return {
			'plugins': {
				'title': 'Plugins (beta)',
				'script': 'pluginloader/plugins.js',
				'tags': ['menu']
			}
		}

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

	def uploadPlugin(self, f):
		with open('%s/staging.zip' % (Board.pluginPath()), 'w') as wf:
			wf.write(f.file.read())

	def matchRequest(self, plugin, path):
		if plugin != 'pluginloader':
			return False
		if path in ['icon','import', 'importkey', 'installStorePlugin', 'keys', 'remove', 'plugins', 'saveConfiguration', 'storePlugins', 'upload']:
			return True
		return False

	def handleRequest(self, plugin, path, params, request, **kwargs):
		if path == 'icon':
			for plugin in Loader(self.context).plugins:
				if plugin.name != params['name']:
					continue
				return WebResponseLocalFile('%s/%s' % (plugin.path, plugin.icon))
			return None

		if path == 'import':
			filename = '%s/staging.zip' % (Board.pluginPath())
			if os.path.isfile(filename):
				try:
					return WebResponseJson(Loader(self.context).importPlugin(filename))
				except ImportError as e:
					os.unlink('%s/staging.zip' % (Board.pluginPath()))
					return WebResponseJson({'success': False, 'msg':'Error importing plugin: %s' % e})
			return WebResponseJson({'success': False, 'msg':'Error importing plugin: No plugin uploaded'})

		if path == 'importkey':
			if 'discard' in params:
				os.unlink('%s/staging.zip' % (Board.pluginPath()))
				return WebResponseJson({'success': True})
			return WebResponseJson(self.importKey(params['key'] if 'key' in params else None))

		if path == 'installStorePlugin':
			if 'pluginname' not in params:
				return WebResponseJson({'success': False, 'msg': 'No plugin specified'})
			for plugin in yaml.load(open('%s/plugins.yml' % Board.pluginPath(), 'r').read()):
				if plugin['name'] == params['pluginname']:
					Loader(self.context).installRemotePlugin(plugin['name'], plugin['file']['url'], plugin['file']['size'], plugin['file']['sha1'])
					return WebResponseJson({'success': True})
			return WebResponseJson({'success': False, 'msg': 'Plugin was not found in the store'})

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

		if path == 'storePlugins':
			if os.path.exists('%s/plugins.yml' % Board.pluginPath()) == False:
				return WebResponseJson([])
			return WebResponseJson([
				{
					'author': plugin['author'],
					'author-email': plugin['author-email'],
					'category': plugin.get('category', 'other'),
					'color': plugin.get('color', None),
					'name': plugin['name'],
					'icon': plugin['icon'] if 'icon' in plugin else '',
					'description': plugin['description'],
					'size': plugin['file']['size'],
					'version': plugin['version'],
				}
				for plugin in yaml.load(open('%s/plugins.yml' % Board.pluginPath(), 'r').read())
			])

		if path == 'upload' and request.method() == 'POST':
			self.uploadPlugin(params['pluginfile'])
			filename = '%s/staging.zip' % (Board.pluginPath())
			try:
				return WebResponseJson(Loader(self.context).importPlugin(filename))
			except ImportError as e:
				os.unlink(filename)
				return WebResponseJson({'success': False, 'msg': str(e)})
