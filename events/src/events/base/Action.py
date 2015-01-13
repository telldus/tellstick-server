# -*- coding: utf-8 -*-

from tellduslive.base import LiveMessage

class Action(object):
	def __init__(self, event, id, *args, **kwargs):
		super(Action,self).__init__()
		self.event = event
		self.id = id

	def execute(self):
		pass

	def loadParams(self, params):
		for param in params:
			self.parseParam(param, params[param])

	def parseParam(self, name, value):
		pass

	def start(self):
		self.execute()

	def triggered(self):
		self.event.execute(self)

class RemoteAction(Action):
	def __init__(self, **kwargs):
		super(RemoteAction,self).__init__(**kwargs)

	def execute(self):
		msg = LiveMessage('event-executeaction')
		msg.append({
			'action': self.id
		})
		self.event.manager.live.send(msg)
