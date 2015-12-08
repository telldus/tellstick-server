# -*- coding: utf-8 -*-

import logging

class Trigger(object):
	def __init__(self, event, id, *args, **kwargs):
		super(Trigger,self).__init__()
		self.event = event
		self.id = id

	def close(self):
		pass

	def loadParams(self, params):
		for param in params:
			try:
				self.parseParam(param, params[param])
			except Exception as e:
				logging.error(str(e))
				logging.error("Could not parse trigger param, %s - %s" % (param, params[param]))

	def parseParam(self, name, value):
		pass

	def triggered(self):
		self.event.execute(self)
