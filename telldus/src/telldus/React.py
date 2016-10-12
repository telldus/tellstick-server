from base import IInterface, ObserverCollection, Plugin, implements
from web.base import IWebRequestHandler, WebResponseHtml, WebResponseJson
from pkg_resources import resource_filename
import logging

class IWebReactHandler(IInterface):
	def getReactRoutes():
		"""Return a list of routes this plugin listens to"""

class React(Plugin):
	implements(IWebRequestHandler)
	observers = ObserverCollection(IWebReactHandler)

	def __init__(self):
		pass

	def getTemplatesDirs(self):
		return [resource_filename('telldus', 'templates')]

	def handleRequest(self, plugin, path, params, request):
		if plugin != 'telldus':
			return None
		if path == 'react':
			return WebResponseHtml('react.html')
		if path == 'reactPlugins':
			plugins = []
			for o in self.observers:
				routes = o.getReactRoutes()
				if type(routes) == list:
					plugins.extend(routes)
				logging.warning("Routes %s", routes)
			return WebResponseJson(plugins)
		return None


	def matchRequest(self, plugin, path):
		if plugin != 'telldus':
			return False
		if path in ['react', 'reactPlugins']:
			return True
		return False
