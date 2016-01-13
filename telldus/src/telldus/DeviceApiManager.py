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
				'type':'device',  # TODO(micke): Implement
			})
		return {'device': retval}

	@apicall('device', 'bell')
	def deviceBell(self, id, **kwargs):
		"""
		Sends bell command to devices supporting this.
		"""
		return self.deviceCommand(id, Device.BELL)

	@apicall('device', 'command')
	def deviceCommand(self, id, method, value=None, **kwargs):
		"""
		Sends a command to a device.
		"""
		device = self.__retrieveDevice(id)
		device.command(method, value, origin='Local API')
		return True

	@apicall('device', 'dim')
	def deviceDim(self, id, level, **kwargs):
		"""
		Sends a dim command to devices supporting this.
		"""
		return self.deviceCommand(id, Device.DIM, level)

	@apicall('device', 'down')
	def deviceDown(self, id, **kwargs):
		"""
		Sends a "down" command to devices supporting this.
		"""
		return self.deviceCommand(id, Device.DOWN)

	@apicall('device', 'info')
	def deviceInfo(self, id, supportedMethods=0, extras=None, **kwargs):
		"""
		Returns information about a specific device.
		"""
		extras = extras.split(',') if extras is not None else []
		device = self.__retrieveDevice(id)
		state, stateValue = device.state()
		retval = {
			'id': device.id(),
			'name': device.name(),
			'state': Device.maskUnsupportedMethods(state, int(supportedMethods)),
			'statevalue': stateValue,
			'methods': Device.maskUnsupportedMethods(device.methods(), int(supportedMethods)),
			'type': 'device',  # TODO(micke): Implement
			'protocol': device.protocol(),
			'model': device.model(),
		}
		if 'transport' in extras:
			retval['transport'] = device.typeString()
		return retval

	@apicall('device', 'learn')
	def deviceLearn(self, id, **kwargs):
		"""
		Sends a special learn command to some devices that need a special
		learn-command to be used from TellStick
		"""
		return self.deviceCommand(id, Device.LEARN)

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

	def __retrieveDevice(self, deviceId):
		deviceManager = DeviceManager(self.context)
		device = deviceManager.device(int(deviceId))
		if device is None:
			raise Exception('Device "%s" could not be found' % deviceId)
		return device
