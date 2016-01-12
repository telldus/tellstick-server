# -*- coding: utf-8 -*-

import logging
from openid.store import memstore
from openid.consumer import consumer
from openid.extensions import sreg

from base import implements, Plugin
try:
	from web.base import IWebRequestHandler, WebResponseRedirect
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
		self.session = {}
		self.store = memstore.MemoryStore()

	def getTemplatesDirs(self):
		return [resource_filename('telldus', 'templates')]

	def matchRequest(self, plugin, path):
		if path == '' and plugin == '':
			return True
		if plugin != 'telldus':
			return False
		if path in ['login', 'authorize']:
			return True
		return False

	def handleRequest(self, plugin, path, params, request, **kwargs):
		if plugin == '' and path == '':
			return 'index.html', {}
		if plugin != 'telldus':
			return None
		oidconsumer = consumer.Consumer(self.session, self.store)
		if path == 'login':
			try:
				authrequest = oidconsumer.begin('http://login.telldus.com')
			except consumer.DiscoveryFailure, exc:
				logging.error(str(exc[0]))
				return None  # TODO(micke): Error
			sregRequest = sreg.SRegRequest(required=['fullname', 'email'])
			authrequest.addExtension(sregRequest)
			trustRoot = request.base()
			returnTo = '%s/telldus/authorize' % request.base()
			url = authrequest.redirectURL(trustRoot, returnTo)
			return WebResponseRedirect(url)
		if path == 'authorize':
			url = '%s/telldus/authorize' % request.base()
			info = oidconsumer.complete(params, url)
			displayIdentifier = info.getDisplayIdentifier()
			if info.status == consumer.FAILURE and displayIdentifier:
				logging.error("Verification of %s failed: %s", displayIdentifier, info.message)
				return None  # TODO(micke): Error
			elif info.status == consumer.SUCCESS:
				sregResp = sreg.SRegResponse.fromSuccessResponse(info)
			else:
				logging.error("Unknown error: %s", info.message)
				return None  # TODO(micke): Error
		return None

	def requireAuthentication(self, plugin, path):
		if plugin == '' and path == '':
			return False
		return True
