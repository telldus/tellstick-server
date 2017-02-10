from base import IInterface, ObserverCollection, Plugin, implements
from web.base import IWebRequestHandler, WebResponseHtml, WebResponseJson
from pkg_resources import resource_filename
import logging

class IWebReactHandler(IInterface):
	def getReactRoutes():
		"""Return a list of routes this plugin listens to"""

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
			if path == 'reactPlugins':
				return WebResponseJson(self.routes())
		fullPath = '/%s/%s' % (plugin, path) if path is not '' else '/%s' % plugin
		for route in self.routes():
			if route['path'] == fullPath:
				return WebResponseHtml('react.html')
		return None

	def matchRequest(self, plugin, path):
		if path == '' and plugin == '':
			return True
		if plugin == 'telldus' and path in ['reactComponents', 'reactPlugins']:
			return True
		# Check if we match a react route
		fullPath = '/%s/%s' % (plugin, path) if path is not '' else '/%s' % plugin
		for route in self.routes():
			if route['path'] == fullPath:
				return True
		return False

	def routes(self):
		plugins = []
		for o in self.observers:
			routes = o.getReactRoutes()
			if type(routes) != list:
				continue
			for route in routes:
				if 'path' not in route:
					route['path'] = '/%s' % route['name']
			plugins.extend(routes)
		return plugins
