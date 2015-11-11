# -*- coding: utf-8 -*-

from base import implements, Plugin
from telldus import DeviceManager, Device
from tellduslive.base import TelldusLive, ITelldusLiveObserver

class GroupDevice(Device):
	def __init__(self):
		super(GroupDevice,self).__init__()
		self._nodeId = 0
		self.devices = []

	def _command(self, action, value, success, failure, ignore, **kwargs):
		for deviceId in self.devices:
			device = self.manager().device(deviceId)
			if not device:
				continue
			device.command(action, value, origin='Group %s' % self.name(), success=None, failure=None, ignore=ignore)
		success()

	def containingDevices(self):
		return self.devices

	def isDevice(self):
		return True

	def isSensor(self):
		return False

	def localId(self):
		return self._nodeId

	def params(self):
		return {
			'devices': self.devices,
		}

	def setId(self, newId):
		self._nodeId = newId
		super(GroupDevice,self).setId(newId)

	def setNodeId(self, nodeId):
		self._nodeId = nodeId

	def setParams(self, params):
		self.devices = params.setdefault('devices', [])

	def typeString(self):
		return 'group'

	def methods(self):
		m = 0
		for device in self.flattenContainingDevices():
			m = m | device.methods()
		return m

class Group(Plugin):
	implements(ITelldusLiveObserver)

	def __init__(self):
		self.devices = []
		self.deviceManager = DeviceManager(self.context)
		for d in self.deviceManager.retrieveDevices('group'):
			p = d.params()
			device = GroupDevice()
			self.devices.append(device)
			device.setNodeId(d.id())
			device.setParams(p)
			self.deviceManager.addDevice(device)
		self.deviceManager.finishedLoading('group')
		self.live = TelldusLive(self.context)

	def addDevice(self, name, devices):
		if type(devices) != list:
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
					device.paramUpdated('')
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
