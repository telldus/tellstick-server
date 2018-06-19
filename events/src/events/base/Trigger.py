# -*- coding: utf-8 -*-

import logging

class Trigger(object):
	# pylint: disable=W0622
	def __init__(self, event, id, *__args, **__kwargs):
		super(Trigger, self).__init__()
		self.event = event
		self.id = id  # pylint: disable=C0103

	def close(self):
		pass

	def loadParams(self, params):
		for param in params:
			try:
				self.parseParam(param, params[param])
			except Exception as error:
				logging.error(str(error))
				logging.error("Could not parse trigger param, %s - %s", param, params[param])

	def parseParam(self, name, value):
		pass

	def triggered(self, triggerInfo=None):
		triggerInfo = triggerInfo or {}
		self.event.execute(self, triggerInfo)
