import os

from base import Plugin, implements
from board import Board
from web.base import IWebRequestHandler, WebResponseJson
from telldus.web import IWebReactHandler

class WebUI(Plugin):
	implements(IWebRequestHandler, IWebReactHandler)

	def __init__(self):
		pass

	@staticmethod
	def getReactComponents():
		retval = {
			'com.telldus.firmware': {
				'title': 'Firmware',
				'builtin': 'FirmwareSettings',
				'tags': ['settings'],
			},
		}
		return retval

	@staticmethod
	def handleRequest(plugin, path, params, **__kwargs):
		if plugin != 'telldus':
			return None

		if path == 'info':
			try:
				with open('/etc/distribution') as fd:
					distribution = fd.readline().strip()
			except Exception as __error:
				distribution = ''
			return WebResponseJson({
				'firmware': {
					'version': Board.firmwareVersion(),
					'distribution': distribution,
				},
			})

		if path == 'setDistribution':
			if params.get('name', '') not in ['beta', 'stable']:
				return WebResponseJson({'success': False, 'error': 'Invalid distribution'})
			retval = os.system('/usr/sbin/telldus-helper distribution %s' % params['name'])
			if retval == 0:
				return WebResponseJson({'success': True})
			return WebResponseJson({'success': False, 'error': 'Could not change the firmware version'})

		return None

	@staticmethod
	def matchRequest(plugin, path):
		if plugin == 'telldus' and path in [
			'info',
			'setDistribution'
		]:
			return True
		return False
