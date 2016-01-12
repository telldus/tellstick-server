# -*- coding: utf-8 -*-

from api import IApiCallHandler, apicall
from base import Plugin, implements
from DeviceManager import DeviceManager

class DeviceApiManager(Plugin):
	implements(IApiCallHandler)

	@apicall('devices', 'list')
	def devicesList(self):
		"""
		Returns a list of all devices
		"""
		deviceManager = DeviceManager(self.context)
		retval = []
		for d in deviceManager.retrieveDevices():
			if not d.isDevice():
				continue
			retval.append({
				'id': d.id(),
				'name': d.name(),
				'state': 0,
				'statevalue': '',
				'methods': 0,
				'type':'device',
			})
		return {'device': retval}
