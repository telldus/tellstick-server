# -*- coding: utf-8 -*-

from api import IApiCallHandler, apicall
from base import Plugin, implements
from Device import Device
from DeviceManager import DeviceManager

class DeviceApiManager(Plugin):
	implements(IApiCallHandler)

	@apicall('devices', 'list')
	def devicesList(self, supportedMethods=0, **kwargs):
		"""
		Returns a list of all devices.
		"""
		deviceManager = DeviceManager(self.context)
		retval = []
		for d in deviceManager.retrieveDevices():
			if not d.isDevice():
				continue
			state, stateValue = d.state()
			retval.append({
				'id': d.id(),
				'name': d.name(),
				'state': Device.maskUnsupportedMethods(state, int(supportedMethods)),
				'statevalue': stateValue,
				'methods': Device.maskUnsupportedMethods(d.methods(), int(supportedMethods)),
				'type':'device',
			})
		return {'device': retval}

	@apicall('device', 'command')
	def deviceCommand(self, id, method, value=None, **kwargs):
		"""
		Sends a command to a device.
		"""
		deviceManager = DeviceManager(self.context)
		device = deviceManager.device(int(id))
		if device is None:
			raise Exception('Device "%s" could not be found' % id)
		device.command(method, value, origin='Local API')
		return True

	@apicall('device', 'turnOff')
	def deviceTurnOff(self, id, **kwargs):
		"""
		Turns a device off.
		"""
		return self.deviceCommand(id, Device.TURNOFF)

	@apicall('device', 'turnOn')
	def deviceTurnOn(self, id, **kwargs):
		"""
		Turns a device on.
		"""
		return self.deviceCommand(id, Device.TURNON)
