from base import Plugin, implements
from board import Board
from web.base import IWebRequestHandler, WebResponseJson
from telldus.web import IWebReactHandler

class WebUI(Plugin):
	implements(IWebRequestHandler, IWebReactHandler)

	def __init__(self):
		pass

	def getReactComponents(self):
		retval = {
			'com.telldus.firmware': {
				'title': 'Firmware',
				'builtin': 'FirmwareSettings',
				'tags': ['settings'],
			},
		}
		return retval

	def handleRequest(self, plugin, path, params, request):
		if plugin != 'telldus':
			return None

		if path == 'info':
			try:
				with open('/etc/distribution') as fd:
					distribution = fd.readline().strip()
			except Exception as __error:
				distribution = 'unknown'
			return WebResponseJson({
				'firmware': {
					'version': Board.firmwareVersion(),
					'distribution': distribution,
				},
			})

		return None

	def matchRequest(self, plugin, path):
		if plugin == 'telldus' and path in [
			'info',
		]:
			return True
		return False
