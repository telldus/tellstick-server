# -*- coding: utf-8 -*-

from base import implements, Plugin
from web.base import IWebRequestHandler
from pkg_resources import resource_filename
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

	def handleRequest(self, plugin, path, params):
		if plugin != '':
			return None
		if path == '':
			return 'index.html', {}
		return None
