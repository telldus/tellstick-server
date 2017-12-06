from base import IInterface, ObserverCollection, Plugin, implements
from web.base import IWebRequestHandler, WebResponseHtml, WebResponseJson
from pkg_resources import resource_filename
import logging

class IWebReactHandler(IInterface):
	def getReactComponents():
		"""Return a list of components this plugin exports"""

class React(Plugin):
	implements(IWebRequestHandler)
	observers = ObserverCollection(IWebReactHandler)

	def __init__(self):
		pass

	def components(self):
		retval = {}
		for o in self.observers:
			components = o.getReactComponents()
			if type(components) != dict:
				continue
				# Make sure defaults exists
			for name in components:
				tags = components[name].setdefault('tags', [])
				if 'menu' in tags:
					components[name].setdefault('path', '/%s' % name)
			retval.update(components)
		return retval

	def getTemplatesDirs(self):
		return [resource_filename('telldus', 'templates')]

	def handleRequest(self, plugin, path, params, request):
		if path == '' and plugin == '':
			return WebResponseHtml('react.html')
		if plugin == 'telldus':
			if path == 'reactComponents':
				return WebResponseJson(self.components())
			if path in ['settings']:
				return WebResponseHtml('react.html')
		fullPath = '/%s/%s' % (plugin, path) if path is not '' else '/%s' % plugin
		components = self.components()
		for name in components:
			if components[name].get('path', None) == fullPath:
				return WebResponseHtml('react.html')
		return None

	def matchRequest(self, plugin, path):
		if path == '' and plugin == '':
			return True
		if plugin == 'telldus' and path in ['reactComponents', 'settings']:
			return True
		# Check if we match a react route
		fullPath = '/%s/%s' % (plugin, path) if path is not '' else '/%s' % plugin
		components = self.components()
		for name in components:
			if components[name].get('path', None) == fullPath:
				return True
		return False
