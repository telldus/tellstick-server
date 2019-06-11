# -*- coding: utf-8 -*-

import datetime

from api import IApiCallHandler, apicall
from base import Plugin, implements
from board import Board
from .Device import Device
from .DeviceManager import DeviceManager

class DeviceApiManager(Plugin):
	implements(IApiCallHandler)

	@apicall('devices', 'list')
	def devicesList(self, supportedMethods=0, **__kwargs):
		"""
		Returns a list of all devices.
		"""
		deviceManager = DeviceManager(self.context)  # pylint: disable=E1121
		retval = []
		for device in deviceManager.retrieveDevices():
			if not device.isDevice():
				continue
			state, stateValue = device.state()
			retval.append({
				'id': device.id(),
				'name': device.name(),
				'state': Device.maskUnsupportedMethods(state, int(supportedMethods)),
				'statevalue': stateValue,
				'methods': Device.maskUnsupportedMethods(device.methods(), int(supportedMethods)),
				'type':'device',  # TODO(micke): Implement
			})
		return {'device': retval}

	@apicall('device', 'bell')
	def deviceBell(self, id, **kwargs):  # pylint: disable=C0103,W0622
		"""
		Sends bell command to devices supporting this.
		"""
		return self.deviceCommand(id, Device.BELL, **kwargs)

	@apicall('device', 'command')
	def deviceCommand(self, id, method, value=None, app=None, **__kwargs):  # pylint: disable=C0103,W0622
		"""
		Sends a command to a device.
		"""
		device = self.__retrieveDevice(id)
		try:
			# Try convering to number if it was sent as such
			method = int(method)
		except ValueError:
			# Not a number, keep it as a string
			pass
		device.command(method, value, origin=app)
		return True

	@apicall('device', 'dim')
	def deviceDim(self, id, level, **kwargs):  # pylint: disable=C0103,W0622
		"""
		Sends a dim command to devices supporting this.
		"""
		return self.deviceCommand(id, Device.DIM, level, **kwargs)

	@apicall('device', 'down')
	def deviceDown(self, id, **kwargs):  # pylint: disable=C0103,W0622
		"""
		Sends a "down" command to devices supporting this.
		"""
		return self.deviceCommand(id, Device.DOWN, **kwargs)

	@apicall('device', 'info')
	def deviceInfo(self, id, supportedMethods=0, extras=None, **__kwargs):  # pylint: disable=C0103,W0622
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
	def deviceLearn(self, id, **kwargs):  # pylint: disable=C0103,W0622
		"""
		Sends a special learn command to some devices that need a special
		learn-command to be used from TellStick
		"""
		return self.deviceCommand(id, Device.LEARN, **kwargs)

	@apicall('device', 'rgb')
	def deviceRGB(self, id, r, g, b, **kwargs):
		"""
		Send a command to change color on a device
		"""
		r = (int(r) & 0xFF) << 16;
		g = (int(g) & 0xFF) << 8;
		b = int(b) & 0xFF;
		color = r | g | b;
		return self.deviceCommand(id, Device.RGB, color)

	@apicall('device', 'setName')
	def deviceSetName(self, id, name, **__kwargs):  # pylint: disable=C0103,W0622
		"""
		Renames a device
		"""
		device = self.__retrieveDevice(id)
		device.setName(str(name))
		return True

	@apicall('device', 'stop')
	def deviceStop(self, id, **kwargs):  # pylint: disable=C0103,W0622
		"""
		Send a "stop" command to device.
		"""
		return self.deviceCommand(id, Device.STOP, **kwargs)

	@apicall('device', 'turnOff')
	def deviceTurnOff(self, id, **kwargs):  # pylint: disable=C0103,W0622
		"""
		Turns a device off.
		"""
		return self.deviceCommand(id, Device.TURNOFF, **kwargs)

	@apicall('device', 'turnOn')
	def deviceTurnOn(self, id, **kwargs):  # pylint: disable=C0103,W0622
		"""
		Turns a device on.
		"""
		return self.deviceCommand(id, Device.TURNON, **kwargs)

	@apicall('device', 'up')
	def deviceUp(self, id, **kwargs):  # pylint: disable=C0103,W0622
		"""
		Send an "up" command to device.
		"""
		return self.deviceCommand(id, Device.UP, **kwargs)

	@apicall('sensors', 'list')
	def sensorsList(self, includeValues=None, includeScale=None, **__kwargs):
		"""Returns a list of all sensors associated with the current user"""
		includeValues = True if includeValues == '1' else False
		includeScale = True if includeScale == '1' else False
		deviceManager = DeviceManager(self.context)  # pylint: disable=E1121
		retval = []
		for device in deviceManager.retrieveDevices():
			if not device.isSensor():
				continue
			sensor = {
				'id': device.id(),
				'name': device.name(),
				#'lastUpdated': 1442561174,  # TODO(micke): Implement when we have this
				'protocol': device.protocol(),
				'model': device.model(),
				'sensorId': device.id()
			}
			battery = device.battery()
			if battery:
				sensor['battery'] = battery
			if includeValues:
				data = []
				for sensorType, values in list(device.sensorValues().items()):
					for value in values:
						if includeScale:
							data.append({
								'name': Device.sensorTypeIntToStr(sensorType),
								'value': value['value'],
								'scale': value['scale'],
								# TODO(micke): Implement this when we have timestamp per value
								#'lastUpdated': 1442561174.4156,
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
	def sensorInfo(self, id, **__kwargs):  # pylint: disable=C0103,W0622
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
					# TODO(micke): Implement this when we have timestamp per value
					#'lastUpdated': 1442561174.4156,
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
	def sensorSetName(self, id, name, **kwargs):  # pylint: disable=C0103,W0622
		"""
		Renames a sensor
		"""
		return self.deviceSetName(id, name, **kwargs)

	@apicall('system', 'info')
	def systemInfo(self, **__kwargs):  # pylint: disable=R0201
		return {
			'product': Board.product(),
			'time': datetime.datetime.now().isoformat(),
			'version': Board.firmwareVersion().strip(),
		}

	def __retrieveDevice(self, deviceId):
		deviceManager = DeviceManager(self.context)  # pylint: disable=E1121
		device = deviceManager.device(int(deviceId))
		if device is None:
			raise Exception('Device "%s" could not be found' % deviceId)
		return device
