# -*- coding: utf-8 -*-

from base import IInterface, ObserverCollection, Plugin, implements
from web.base import IWebRequestHandler, WebResponseJson
from pkg_resources import resource_filename
import logging

class IApiCallHandler(IInterface):
	"""IInterface for plugin implementing API calls"""

class ApiManager(Plugin):
	implements(IWebRequestHandler)

	observers = ObserverCollection(IApiCallHandler)

	def matchRequest(self, plugin, path):
		if plugin != 'api':
			return False
		if path.startswith('json/'):
			return True
		return False

	def handleRequest(self, plugin, path, params, **kwargs):
		paths = path.split('/')
		if len(paths) < 3:
			return None
		returnFormat = paths[0]
		module = paths[1]
		action = paths[2]
		for o in self.observers:
			fn = getattr(o, '_apicalls', {}).get(module, {}).get(action, None)
			if fn is None:
				continue
			try:
				retval = fn(o, **params)
			except Exception as e:
				logging.exception(e)
				return WebResponseJson({'error': str(e)})
			return WebResponseJson(retval)
		return None

	@staticmethod
	def apicall(module, action):
		def call(fn):
			import sys
			frame = sys._getframe(1)
			frame.f_locals.setdefault('_apicalls', {}).setdefault(module, {})[action] = fn
			return fn
		return call

apicall = ApiManager.apicall
