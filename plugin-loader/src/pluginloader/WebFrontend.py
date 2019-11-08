# -*- coding: utf-8 -*-

from base import Plugin, implements
from board import Board
from web.base import IWebRequestHandler, WebResponseLocalFile, WebResponseJson, WebResponseRedirect
from telldus.web import IWebReactHandler
import json
import os
import yaml
from pluginloader.Loader import Loader
import gnupg

def loadGPG():
	return gnupg.GPG(keyring='%s/plugins.keyring' % Board.pluginPath())

class WebFrontend(Plugin):
	implements(IWebRequestHandler)
	implements(IWebReactHandler)

	def getReactComponents(self):  # pylint: disable=R0201
		return {
			'plugins': {
				'title': 'Plugins (beta)',
				'script': 'pluginloader/plugins.js',
				'tags': ['menu']
			},
			'plugins/oauth2': {
				'script': 'pluginloader/oauth2.js'
			}
		}

	def matchRequest(self, plugin, path):  # pylint: disable=R0201
		if plugin != 'pluginloader':
			return False
		if path in [
			'oauth2',
			'icon',
			'import',
			'importkey',
			'installStorePlugin',
			'keys',
			'reboot',
			'refreshStorePlugins',
			'remove',
			'plugins',
			'saveConfiguration',
			'storePlugins',
			'upload'
		]:
			return True
		return False

	def handleOauth2Request(self, params, request):
		plugin = params['pluginname']
		pluginClass = params['pluginclass']
		pluginConfig = params['config']
		configuration = Loader(self.context).configurationForPlugin(plugin, pluginClass, pluginConfig)
		if not configuration:
			return WebResponseJson({'success': False, 'msg': 'Configuration not found'})
		if 'code' not in params:
			redirectUri = params['redirectUri']
			if not hasattr(configuration, 'activate'):
				return WebResponseJson({'success': False, 'msg': 'Configuration cannot be activated'})
			url = configuration.activate(redirectUri)
			return WebResponseJson({'success': True, 'url': url})
		params = configuration.activateCode(params['code'])
		try:
			config = {
				pluginClass: {
					pluginConfig: params
				}
			}
			Loader(self.context).saveConfiguration(plugin, config)
		except Exception as error:
			return WebResponseJson({'success': False, 'msg': str(error)})
		return WebResponseRedirect('%s/plugins?settings=%s' % (request.base(), plugin))

	def handleRequest(self, plugin, path, params, request, **kwargs):
		del kwargs
		if path == 'oauth2':
			return self.handleOauth2Request(params, request)

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
				except ImportError as error:
					os.unlink('%s/staging.zip' % (Board.pluginPath()))
					return WebResponseJson({'success': False, 'msg':'Error importing plugin: %s' % error})
			return WebResponseJson({'success': False, 'msg':'Error importing plugin: No plugin uploaded'})

		if path == 'importkey':
			if 'discard' in params:
				os.unlink('%s/staging.zip' % (Board.pluginPath()))
				return WebResponseJson({'success': True})
			return WebResponseJson(Loader(self.context).importKey(
				params['key'] if 'key' in params else None)
			)

		if path == 'installStorePlugin':
			if 'pluginname' not in params:
				return WebResponseJson({'success': False, 'msg': 'No plugin specified'})
			for plugin in yaml.load(open('%s/plugins.yml' % Board.pluginPath(), 'r').read()):
				if plugin['name'] == params['pluginname']:
					Loader(self.context).installRemotePlugin(
						plugin['name'],
						plugin['file']['url'],
						plugin['file']['size'],
						plugin['file']['sha1']
					)
					return WebResponseJson({'success': True})
			return WebResponseJson({'success': False, 'msg': 'Plugin was not found in the store'})

		if path == 'reboot':
			retval = os.system('/usr/sbin/telldus-helper reboot')
			if retval == 0:
				return WebResponseJson({'success': True})
			return WebResponseJson({'success': False})

		if path == 'refreshStorePlugins':
			Loader(self.context).updatePluginsList()
			return WebResponseJson({'success': True})

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
			except Exception as error:
				return WebResponseJson({'success': False, 'msg': str(error)})
			return WebResponseJson({'success': True})

		if path == 'storePlugins':
			if not os.path.exists('%s/plugins.yml' % Board.pluginPath()):
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
			except ImportError as error:
				os.unlink(filename)
				return WebResponseJson({'success': False, 'msg': str(error)})

	@staticmethod
	def uploadPlugin(fileobject):
		with open('%s/staging.zip' % (Board.pluginPath()), 'wb') as fd:
			fd.write(fileobject.file.read())
