# -*- coding: utf-8 -*-

from base import Plugin, implements
from events.base import IEventFactory, Action, Condition, Trigger
from Device import Device
from DeviceManager import DeviceManager, IDeviceChange

class DeviceEventFactory(Plugin):
	implements(IEventFactory)
	implements(IDeviceChange)

	def __init__(self):
		self.triggers = []
		self.deviceManager = DeviceManager(self.context)

	def createAction(self, type, params, **kwargs):
		if type == 'device':
			if 'local' in params and params['local'] == 1:
				return DeviceAction(manager = self.deviceManager, **kwargs)
		return None

	def createCondition(self, type, params, **kwargs):
		if type == 'device':
			if 'local' in params and params['local'] == 1:
				return DeviceCondition(manager = self.deviceManager, **kwargs)
		return None

	def createTrigger(self, type, **kwargs):
		if type == 'device':
			trigger = DeviceTrigger(**kwargs)
			self.triggers.append(trigger)
			return trigger
		return None

	def stateChanged(self, device, method, statevalue):
		for trigger in self.triggers:
			if trigger.deviceId == device.id() and trigger.method == int(method):
				trigger.triggered()

class DeviceAction(Action):
	def __init__(self, manager, **kwargs):
		super(DeviceAction,self).__init__(**kwargs)
		self.manager = manager
		self.deviceId = 0
		self.method = 0
		self.repeats = 1
		self.value = ''

	def parseParam(self, name, value):
		if name == 'clientDeviceId':
			self.deviceId = int(value)
		elif name == 'method':
			self.method = int(value)
		elif name == 'repeats':
			self.repeats = min(10, max(1, int(value)))
		elif name == 'value':
			self.value = int(value)

	def execute(self):
		device = self.manager.device(self.deviceId)
		if device is None:
			return
		m = None
		if self.method == Device.TURNON:
			m = 'turnon'
		elif self.method == Device.TURNOFF:
			m = 'turnoff'
		elif self.method == Device.DIM:
			m = 'dim'
		device.command(m, self.value, origin='Event')

class DeviceCondition(Condition):
	def __init__(self, manager, **kwargs):
		super(DeviceCondition,self).__init__(**kwargs)
		self.manager = manager
		self.deviceId = 0
		self.method = 0

	def parseParam(self, name, value):
		if name == 'clientDeviceId':
			self.deviceId = int(value)
		elif name == 'method':
			self.method = int(value)

	def validate(self, success, failure):
		device = self.manager.device(self.deviceId)
		if device is None:
			failure()
			return
		(state, stateValue) = device.state()
		if state == self.method:
			success()
		else:
			failure()

class DeviceTrigger(Trigger):
	def __init__(self, **kwargs):
		super(DeviceTrigger,self).__init__(**kwargs)
		self.deviceId = 0
		self.method = 0

	def parseParam(self, name, value):
		if name == 'clientDeviceId':
			self.deviceId = int(value)
		elif name == 'method':
			self.method = int(value)
