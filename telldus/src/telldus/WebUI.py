# -*- coding: utf-8 -*-

from base import implements, Plugin
try:
	from web.base import IWebRequestHandler
except ImportError:
	# No webserver available
	from base import IInterface as IWebRequestHandler
try:
	from pkg_resources import resource_filename
except ImportError:
	def pkg_resources():
		return None
from DeviceManager import DeviceManager

class WebUI(Plugin):
	implements(IWebRequestHandler)
	def __init__(self):
		self.deviceManager = DeviceManager(self.context)

	def getTemplatesDirs(self):
		return [resource_filename('telldus', 'templates')]

	def matchRequest(self, plugin, path):
		if path == '' and plugin == '':
			return True
		return False

	def handleRequest(self, plugin, path, params, **kwargs):
		if plugin != '':
			return None
		if path == '':
			return 'index.html', {}
		return None

	def requireAuthentication(self, plugin, path):
		if plugin == '' and path == '':
			return False
