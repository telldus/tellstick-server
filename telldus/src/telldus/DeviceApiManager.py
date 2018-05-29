# -*- coding: utf-8 -*-

from api import IApiCallHandler, apicall
from base import Plugin, implements
from .Device import Device
from .DeviceManager import DeviceManager

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
		return self.deviceCommand(id, Device.BELL, **kwargs)

	@apicall('device', 'command')
	def deviceCommand(self, id, method, value=None, app=None, **kwargs):
		"""
		Sends a command to a device.
		"""
		device = self.__retrieveDevice(id)
		try:
			# Try convering to number if it was sent as such
			value = int(value)
		except ValueError:
			# Not a number, keep it as a string
			pass
		device.command(method, value, origin=app)
		return True

	@apicall('device', 'dim')
	def deviceDim(self, id, level, **kwargs):
		"""
		Sends a dim command to devices supporting this.
		"""
		return self.deviceCommand(id, Device.DIM, level, **kwargs)

	@apicall('device', 'down')
	def deviceDown(self, id, **kwargs):
		"""
		Sends a "down" command to devices supporting this.
		"""
		return self.deviceCommand(id, Device.DOWN, **kwargs)

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
		return self.deviceCommand(id, Device.LEARN, **kwargs)

	@apicall('device', 'setName')
	def deviceSetName(self, id, name, **kwargs):
		"""
		Renames a device
		"""
		device = self.__retrieveDevice(id)
		device.setName(str(name))
		return True

	@apicall('device', 'stop')
	def deviceStop(self, id, **kwargs):
		"""
		Send a "stop" command to device.
		"""
		return self.deviceCommand(id, Device.STOP, **kwargs)

	@apicall('device', 'turnOff')
	def deviceTurnOff(self, id, **kwargs):
		"""
		Turns a device off.
		"""
		return self.deviceCommand(id, Device.TURNOFF, **kwargs)

	@apicall('device', 'turnOn')
	def deviceTurnOn(self, id, **kwargs):
		"""
		Turns a device on.
		"""
		return self.deviceCommand(id, Device.TURNON, **kwargs)

	@apicall('device', 'up')
	def deviceUp(self, id, **kwargs):
		"""
		Send an "up" command to device.
		"""
		return self.deviceCommand(id, Device.UP, **kwargs)

	@apicall('sensors', 'list')
	def sensorsList(self, includeValues=None, includeScale=None, **kwargs):
		"""Returns a list of all sensors associated with the current user"""
		includeValues = True if includeValues == '1' else False
		includeScale = True if includeScale == '1' else False
		deviceManager = DeviceManager(self.context)
		retval = []
		for d in deviceManager.retrieveDevices():
			if not d.isSensor():
				continue
			sensor = {
				'id': d.id(),
				'name': d.name(),
				#'lastUpdated': 1442561174,  # TODO(micke): Implement when we have this
				'protocol': d.protocol(),
				'model': d.model(),
				'sensorId': d.id()
			}
			battery = d.battery()
			if battery:
				sensor['battery'] = battery
			if includeValues:
				data = []
				for sensorType, values in list(d.sensorValues().items()):
					for value in values:
						if includeScale:
							data.append({
								'name': Device.sensorTypeIntToStr(sensorType),
								'value': value['value'],
								'scale': value['scale'],
								#'lastUpdated': 1442561174.4156,  # TODO(micke): Implement this when we have timestamp per value
								#'max': 0.0,  # TODO(micke): Implement when we have min/max for sensors
								#'maxTime': 1442561174.4155,
							})
						else:
							sensor[Device.sensorTypeIntToStr(sensorType)] = value['value']
							break
				if includeScale:
					sensor['data'] = data
			else:
				sensor['novalues'] = True
			retval.append(sensor)
		return {'sensor': retval}

	@apicall('sensor', 'info')
	def sensorInfo(self, id, **kwargs):
		"""
		Returns information about a specific sensor.
		"""
		device = self.__retrieveDevice(id)
		sensorData = []
		for sensorType, values in list(device.sensorValues().items()):
			for value in values:
				sensorData.append({
					'name': Device.sensorTypeIntToStr(sensorType),
					'value': float(value['value']),
					'scale': int(value['scale']),
					#'lastUpdated': 1442561174.4156,  # TODO(micke): Implement this when we have timestamp per value
					#'max': 0.0,  # TODO(micke): Implement when we have min/max for sensors
					#'maxTime': 1442561174.4155,
				})
		return {
			'id': device.id(),
			'name': device.name(),
			#'lastUpdated':1452632383,  # TODO(micke): See sensors/list
			'data': sensorData,
			'protocol': device.protocol(),
			'model': device.model(),
			'sensorId': device.id()
		}

	@apicall('sensor', 'setName')
	def sensorSetName(self, id, name, **kwargs):
		"""
		Renames a sensor
		"""
		return self.deviceSetName(id, name, **kwargs)

	def __retrieveDevice(self, deviceId):
		deviceManager = DeviceManager(self.context)
		device = deviceManager.device(int(deviceId))
		if device is None:
			raise Exception('Device "%s" could not be found' % deviceId)
		return device
