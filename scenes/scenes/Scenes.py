# -*- coding: utf-8 -*-

from base import implements, Plugin, ConfigurationList, configuration
from telldus import DeviceManager, Device
from tellduslive.base import TelldusLive, ITelldusLiveObserver
import uuid

__name__ = 'scenes'

class SceneDevice(Device):
	def __init__(self, uuid):
		super(SceneDevice,self).__init__()
		self._nodeId = uuid
		self.devices = []

	def _command(self, action, value, success, failure, ignore, **kwargs):
		for deviceId in self.devices:
			device = self.manager().device(int(deviceId))
			if not device:
				continue
			data = self.devices[deviceId]
			device.command(data['method'], data['value'], origin='Scene %s' % self.name(), success=None, failure=None, ignore=ignore)
		success()

	def containingDevices(self):
		return self.devices.keys()

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

	def setParams(self, params):
		self.devices = params.setdefault('devices', [])

	def typeString(self):
		return 'scene'

	def methods(self):
		return Device.TURNON


@configuration(
	scenes = ConfigurationList()
)
class SceneManager(Plugin):
	implements(ITelldusLiveObserver)

	def __init__(self):
		self.scenes = {}

		self.deviceManager = DeviceManager(self.context)
		for sceneId in self.config('scenes'):
			device = SceneDevice(sceneId)
			self.scenes[sceneId] = device
			self.deviceManager.addDevice(device)
		self.deviceManager.finishedLoading('scene')

	def addDevice(self, name, devices):
		if type(devices) != dict:
			return
		sceneId = str(uuid.uuid4())
		device = SceneDevice(sceneId)
		device.setName(name)
		device.setParams({
			'devices': devices
		})
		self.scenes[sceneId] = device
		self.deviceManager.addDevice(device)
		scenes = self.config('scenes')
		scenes.append(sceneId)
		self.setConfig('scenes', scenes)

	@TelldusLive.handler('scene')
	def __handleCommand(self, msg):
		data = msg.argument(0).toNative()
		action = data['action']
		if action == 'addScene':
			self.addDevice(data['name'], data['devices'])

		elif action == 'editScene':
			deviceId = data['device']
			for sceneId in self.scenes:
				device  = self.scenes[sceneId]
				if device.id() == deviceId:
					device.setParams({
						'devices': data['devices'],
					})
					device.paramUpdated('')
					break

		elif action == 'sceneInfo':
			deviceId = data['device']
			for sceneId in self.scenes:
				device = self.scenes[sceneId]
				if device.id() == deviceId:
					params = device.params()
					params['deviceId'] = deviceId
					live = TelldusLive(self.context)
					live.pushToWeb('scene', 'sceneInfo', params)
					return

		elif action == 'remove':
			deviceId = data['device']
			for sceneId in self.scenes:
				device = self.scenes[sceneId]
				if device.id() == deviceId:
					self.deviceManager.removeDevice(deviceId)
					del self.scenes[sceneId]
					return
