from base import Plugin, implements
from web.base import IWebRequestHandler, WebResponseJson
from telldus.web import IWebReactHandler

class WebUI(Plugin):
	implements(IWebRequestHandler, IWebReactHandler)

	def __init__(self):
		pass

	def getReactComponents(self):
		retval = {
		}
		return retval

	def handleRequest(self, plugin, path, params, request):
		if plugin != 'telldus':
			return None

		if path == 'info':
			return WebResponseJson({
			})

		return None

	def matchRequest(self, plugin, path):
		if plugin == 'telldus' and path in [
			'info',
		]:
			return True
		return False
