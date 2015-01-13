# -*- coding: utf-8 -*-

from Trigger import Trigger

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

	def triggerDeviceState(self, device, method, statevalue):
		try:
			if self.deviceId == device.id() and self.method == int(method):
				self.triggered()
		except:
			pass
