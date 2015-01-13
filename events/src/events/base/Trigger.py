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

	def triggered(self):
		self.event.execute(self)
