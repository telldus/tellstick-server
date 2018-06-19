# -*- coding: utf-8 -*-

import logging
import time

from tellduslive.base import LiveMessage

class Condition(object):
	# pylint: disable=W0622
	def __init__(self, event, id, group, **__kwargs):
		super(Condition, self).__init__()
		self.event = event
		self.id = id  # pylint: disable=C0103
		self.group = group

	def loadParams(self, params):
		for param in params:
			try:
				self.parseParam(param, params[param])
			except Exception as error:
				logging.error(str(error))
				logging.error("Could not parse condition param, %s - %s", param, params[param])

	def parseParam(self, name, value):
		pass

	@staticmethod
	def validate(success, failure):
		del success
		failure()

class RemoteCondition(Condition):
	def __init__(self, **kwargs):
		super(RemoteCondition, self).__init__(**kwargs)
		self.outstandingRequests = []

	def receivedResultFromServer(self, result):
		for request in self.outstandingRequests:
			age = time.time() - request['started']
			if age > 30:
				# Too old
				continue
			if result == 'success':
				request['success']()
			else:
				request['failure']()
		self.outstandingRequests = []

	def validate(self, success, failure):
		self.outstandingRequests.append({
			'started': time.time(),
			'success': success,
			'failure': failure,
		})
		msg = LiveMessage('event-validatecondition')
		msg.append({
			'condition': self.id
		})
		self.event.manager.live.send(msg)
