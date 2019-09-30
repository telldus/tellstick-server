# -*- coding: utf-8 -*-

from base import implements, Plugin
from telldus import DeviceManager, Device
from tellduslive.base import TelldusLive, ITelldusLiveObserver

class GroupDevice(Device):
	def __init__(self):
		super(GroupDevice, self).__init__()
		self._nodeId = 0
		self.devices = []

	def _command(self, action, value, success, failure, ignore, **__kwargs):
		del failure
		for deviceId in self.devices:
			device = self.manager().device(deviceId)
			if not device:
				continue
			device.command(
				action,
				value,
				origin='Group %s' % self.name(),
				success=None,
				failure=None,
				ignore=ignore
			)
		success()

	def containingDevices(self):
		return self.devices

	@staticmethod
	def deviceType():
		return Device.TYPE_CONTAINER

	@staticmethod
	def isDevice():
		return True

	@staticmethod
	def isSensor():
		return False

	def localId(self):
		return self._nodeId

	def parameters(self):
		return {
			'devices': list(self.devices),  # Return copy
		}

	def params(self):
		return {
			'devices': self.devices,
		}

	def setId(self, newId):
		self._nodeId = newId
		super(GroupDevice, self).setId(newId)

	def setNodeId(self, nodeId):
		self._nodeId = nodeId

	def setParameter(self, name, value):
		if name != 'devices':
			return
		self.devices = [int(x) for x in value.split(',')]
		self.paramUpdated('devices')

	def setParams(self, params):
		self.devices = params.setdefault('devices', [])

	@staticmethod
	def typeString():
		return 'group'

	def methods(self):
		methods = 0
		for device in self.flattenContainingDevices():
			methods = methods | device.methods()
		return methods

class Group(Plugin):
	implements(ITelldusLiveObserver)

	def __init__(self):
		self.devices = []
		self.deviceManager = DeviceManager(self.context)
		for oldDevice in self.deviceManager.retrieveDevices('group'):
			params = oldDevice.params()
			device = GroupDevice()
			self.devices.append(device)
			device.setNodeId(oldDevice.id())
			device.setParams(params)
			self.deviceManager.addDevice(device)
		self.deviceManager.finishedLoading('group')
		self.live = TelldusLive(self.context)

	def addDevice(self, name, devices):
		if not isinstance(devices, list):
			return
		device = GroupDevice()
		device.setName(name)
		device.setParams({
			'devices': devices
		})
		self.devices.append(device)
		self.deviceManager.addDevice(device)

	@TelldusLive.handler('group')
	def __handleCommand(self, msg):
		data = msg.argument(0).toNative()
		action = data['action']
		if action == 'addGroup':
			self.addDevice(data['name'], data['devices'])

		elif action == 'editGroup':
			deviceId = data['device']
			for device in self.devices:
				if device.id() == deviceId:
					device.setParams({
						'devices': data['devices'],
					})
					device.paramUpdated('devices')
					break

		elif action == 'groupInfo':
			deviceId = data['device']
			for device in self.devices:
				if device.id() == deviceId:
					params = device.params()
					params['deviceId'] = deviceId
					self.live.pushToWeb('group', 'groupInfo', params)
					return

		elif action == 'remove':
			deviceId = data['device']
			for device in self.devices:
				if device.id() == deviceId:
					self.deviceManager.removeDevice(deviceId)
					self.devices.remove(device)
					return
