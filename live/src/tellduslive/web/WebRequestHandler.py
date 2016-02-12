# -*- coding: utf-8 -*-

import logging
from openid.store import memstore
from openid.consumer import consumer
from openid.extensions import sreg

from base import implements, Plugin
from tellduslive.base import TelldusLive
try:
	from web.base import IWebRequestHandler, IWebRequestAuthenticationHandler, WebResponseRedirect
except ImportError:
	# No webserver available
	from base import IInterface as IWebRequestHandler
try:
	from pkg_resources import resource_filename
except ImportError:
	def pkg_resources():
		return None

class WebRequestHandler(Plugin):
	implements(IWebRequestHandler, IWebRequestAuthenticationHandler)

	def __init__(self):
		self.store = memstore.MemoryStore()

	def getTemplatesDirs(self):
		return [resource_filename('tellduslive', 'web/templates')]

	def isUrlAuthorized(self, request):
		return request.session('loggedIn', False)

	def handleAuthenticationForUrl(self, request):
		return False

	def handleRequest(self, plugin, path, params, request, **kwargs):
		if plugin != 'tellduslive':
			return None
		oidconsumer = consumer.Consumer({}, self.store)
		if path == 'login':
			try:
				authrequest = oidconsumer.begin('http://login.telldus.com')
			except consumer.DiscoveryFailure, exc:
				logging.error(str(exc[0]))
				return None  # TODO(micke): Error
			sregRequest = sreg.SRegRequest(required=['fullname', 'email'])
			authrequest.addExtension(sregRequest)
			trustRoot = request.base()
			returnTo = '%s/tellduslive/authorize' % request.base()
			url = authrequest.redirectURL(trustRoot, returnTo)
			return WebResponseRedirect(url)
		if path == 'authorize':
			url = '%s/tellduslive/authorize' % request.base()
			info = oidconsumer.complete(params, url)
			displayIdentifier = info.getDisplayIdentifier()
			if info.status == consumer.FAILURE and displayIdentifier:
				return None  # TODO(micke): Error
			elif info.status == consumer.SUCCESS:
				sregResp = sreg.SRegResponse.fromSuccessResponse(info)
				data = dict(sregResp.items())
				if 'email' not in data:
					return None  # TODO(micke): Error
				tellduslive = TelldusLive(self.context)
				if data['email'] != tellduslive.email:
					return 'loginFailed.html', {'reason': 1, 'loginEmail': data['email'], 'registeredEmail': tellduslive.email}
				request.setSession('loggedIn', True)
				return request.loggedIn()
			else:
				return None  # TODO(micke): Error
		return None

	def loginProvider(self):
		return {'name': 'Telldus Live!', 'url': '/tellduslive/login'}

	def matchRequest(self, plugin, path):
		if plugin != 'tellduslive':
			return False
		if path in ['authorize', 'login']:
			return True
		return False

	def requireAuthentication(self, plugin, path):
		if plugin == 'tellduslive' and path in ['login', 'authorize']:
			return False
		return True
