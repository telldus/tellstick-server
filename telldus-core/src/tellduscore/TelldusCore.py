# -*- coding: utf-8 -*-

from base import Application, Plugin, implements
from telldus import DeviceManager, Device, IDeviceChange
from .ConnectionListener import ConnectionListener

class TelldusCore(Plugin):
	TELLSTICK_SUCCESS = 0
	TELLSTICK_ERROR_DEVICE_NOT_FOUND = -3
	TELLSTICK_ERROR_UNKNOWN = -99

	implements(IDeviceChange)

	def __init__(self):
		self.deviceManager = DeviceManager(self.context)
		self.clientListener = ConnectionListener('TelldusClient', self.clientMessage)
		self.events = ConnectionListener('TelldusEvents', self.eventMessage)
		Application().registerShutdown(self.shutdown)

	def clientMessage(self, client, msg):
		(func, msg) = TelldusCore.takeString(msg)

		if func == 'tdTurnOn':
			self.doCommand(msg, 'turnon', client)
		elif func == 'tdTurnOff':
			self.doCommand(msg, 'turnoff', client)
		elif func == 'tdBell':
			self.doCommand(msg, '', client)
		#elif func == 'tdDim':
			#pass
		elif func == 'tdExecute':
			self.doCommand(msg, 'execute', client)
		elif func == 'tdUp':
			self.doCommand(msg, 'up', client)
		elif func == 'tdDown':
			self.doCommand(msg, 'down', client)
		elif func == 'tdStop':
			self.doCommand(msg, 'stop', client)
		elif func == 'tdLearn':
			self.doCommand(msg, 'learn', client)
		elif func == 'tdLastSentCommand':
			(deviceId, msg) = TelldusCore.takeInt(msg)
			(supportedMethods, msg) = TelldusCore.takeInt(msg)
			device = self.deviceManager.device(deviceId)
			if not device:
				client.respond(TelldusCore.TELLSTICK_ERROR_DEVICE_NOT_FOUND)
			state, stateValue = device.state()
			client.respond(Device.maskUnsupportedMethods(state, supportedMethods))
		#elif func == 'tdLastSentValue':
			#pass
		elif func == 'tdGetNumberOfDevices':
			client.respond(len(self.__filteredDevices()))
		elif func == 'tdGetDeviceId':
			(deviceIndex, msg) = TelldusCore.takeInt(msg)
			deviceList = self.__filteredDevices()
			if deviceIndex > len(deviceList) - 1:
				client.respond(TelldusCore.TELLSTICK_ERROR_DEVICE_NOT_FOUND)
			device = deviceList[deviceIndex]
			client.respond(device.id())
		#elif func == 'tdGetDeviceType':
			#pass
		elif func == 'tdGetName':
			(deviceId, msg) = TelldusCore.takeInt(msg)
			device = self.deviceManager.device(deviceId)
			if not device:
				client.respond('')
			client.respond(device.name())
		#elif func == 'tdSetName':
			#pass
		#elif func == 'tdGetProtocol':
			#pass
		#elif func == 'tdSetProtocol':
			#pass
		#elif func == 'tdGetModel':
			#pass
		#elif func == 'tdSetModel':
			#pass
		#elif func == 'tdGetDeviceParameter':
			#pass
		#elif func == 'tdSetDeviceParameter':
			#pass
		#elif func == 'tdAddDevice':
			#pass
		#elif func == 'tdRemoveDevice':
			#pass
		elif func == 'tdMethods':
			(deviceId, msg) = TelldusCore.takeInt(msg)
			(supportedMethods, msg) = TelldusCore.takeInt(msg)
			device = self.deviceManager.device(deviceId)
			if not device:
				client.respond(TelldusCore.TELLSTICK_ERROR_DEVICE_NOT_FOUND)
			client.respond(Device.maskUnsupportedMethods(device.methods(), supportedMethods))
		#elif func == 'tdSendRawCommand':
			#pass
		#elif func == 'tdConnectTellStickController':
			#pass
		#elif func == 'tdDisconnectTellStickController':
			#pass
		#elif func == 'tdSensor':
			#pass
		#elif func == 'tdSensorValue':
			#pass
		#elif func == 'tdController':
			#pass
		#elif func == 'tdControllerValue':
			#pass
		#elif func == 'tdSetControllerValue':
			#pass
		#elif func == 'tdRemoveController':
			#pass
		else:
			client.respond(TelldusCore.TELLSTICK_ERROR_UNKNOWN)

	def doCommand(self, msg, action, client):
		(deviceId, msg) = TelldusCore.takeInt(msg)
		device = self.deviceManager.device(deviceId)
		if device is None:
			client.respond(TelldusCore.TELLSTICK_ERROR_DEVICE_NOT_FOUND)
		device.command(action, origin='TelldusCore')
		client.respond(TelldusCore.TELLSTICK_SUCCESS)

	def eventMessage(self, client, msg):
		pass

	def shutdown(self):
		self.clientListener.close()
		self.events.close()

	def stateChanged(self, device, method, statevalue):
		if statevalue is None:
			statevalue = ''
		self.events.broadcast('TDDeviceEvent', device.id(), method, statevalue)

	def __filteredDevices(self):
		return [x for x in self.deviceManager.devices if x.isDevice()]

	@staticmethod
	def takeInt(msg):
		if msg[0] != 'i':
			return ('', msg)
		index = msg.find('s')
		if (index < 0):
			return ('', msg)
		try:
			value = int(msg[1:index], 10)
		except:
			return ('', msg)
		return (value, msg[index+1:])

	@staticmethod
	def takeString(msg):
		if not msg[0].isdigit():
			return ('', msg)
		index = msg.find(':')
		if (index < 0):
			return ('', msg)
		try:
			length = int(msg[:index], 10)
		except:
			return ('', msg)
		value = msg[index+1:index+length+1]
		return (value, msg[index+length+1:])
