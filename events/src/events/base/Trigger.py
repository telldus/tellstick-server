# -*- coding: utf-8 -*-

class Trigger(object):
	def __init__(self, event, id, *args, **kwargs):
		super(Trigger,self).__init__()
		self.event = event
		self.id = id

	def loadParams(self, params):
		for param in params:
			self.parseParam(param, params[param])

	def parseParam(self, name, value):
		pass

	@staticmethod
	def load(type, **kwargs):
		if type == 'device':
			return DeviceTrigger(**kwargs)
		return None

	def triggered(self):
		self.event.execute(self)

from DeviceTrigger import DeviceTrigger
