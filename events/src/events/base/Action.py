# -*- coding: utf-8 -*-

from base import Application, mainthread, Settings
from tellduslive.base import LiveMessage
from threading import Timer
import logging
import time

class Action(object):
	def __init__(self, event, id, delay, delayPolicy, delayExecTime=None, *args, **kwargs):
		super(Action,self).__init__()
		self.event = event
		self.id = id
		self.delay = delay
		self.delayPolicy = delayPolicy
		self.delayExecTime = None
		if delayExecTime:
			self.delayExecTime = float(delayExecTime)
		self.timeout = None
		self.s = Settings('telldus.event')
		Application().registerShutdown(self.stop)

	def close(self):
		if self.timeout:
			self.timeout.cancel()

	def compareStoredDelay(self, storedActions):
		if not storedActions or str(self.id) not in storedActions:
			return
		storedAction = storedActions[str(self.id)]
		if 'delayExecTime' not in storedAction or storedAction['delay'] != self.delay or self.delayPolicy != "continue" or storedAction['delayPolicy'] != self.delayPolicy:
			return
		# action is waiting for a delay, and delaytime or delaypolicy hasn't been changed, so readd this delay
		self.delayExecTime = float(storedAction['delayExecTime'])
		if self.delayExecTime < (time.time() - 900):
			# to late to execute this delayed action now, just ignore it
			self.delayExecTime = None
			self.updateStoredAction()
		elif self.delayExecTime < time.time():
			# execute it now, it's within the correct interval
			self.executeDelayed()
		else:
			# still waiting to execute this action, start a new delayTimer
			if self.timeout:
				self.timeout.cancel()
			self.timeout = Timer(self.delayExecTime - time.time(), self.executeDelayed)
			self.timeout.start()

	def execute(self):
		pass

	def executeDelayed(self):
		self.delayExecTime = None
		self.updateStoredAction()
		self.execute()

	def loadParams(self, params):
		for param in params:
			try:
				self.parseParam(param, params[param])
			except Exception as e:
				logging.error(str(e))
				logging.error("Could not parse action param, %s - %s" % (param, params[param]))

	def parseParam(self, name, value):
		pass

	def start(self):
		if self.delay == 0:
			self.execute()
			return
		else:
			if self.delayPolicy == "continue" and self.delayExecTime:
				# already waiting for this action, do nothing
				return
		if self.timeout:
			self.timeout.cancel()
		self.timeout = Timer(self.delay, self.executeDelayed)
		self.timeout.start()
		self.delayExecTime = time.time() + self.delay
		self.updateStoredAction()

	def stop(self):
		if self.timeout:
			self.timeout.cancel()

	def triggered(self):
		self.event.execute(self)

	@mainthread
	def updateStoredAction(self):
		storeddata = self.s.get('events', {})
		eventId = str(self.event.eventId)
		if eventId in storeddata:
			if 'actions' in storeddata[eventId]:
				actions = storeddata[eventId]['actions']
				if str(self.id) in actions:
					action = actions[str(self.id)]
					if self.delayExecTime:
						action['delayExecTime'] = self.delayExecTime
					else:
						try:
							del action['delayExecTime']
						except Exception as e:
							pass
		self.s['events'] = storeddata

class RemoteAction(Action):
	def __init__(self, **kwargs):
		super(RemoteAction,self).__init__(**kwargs)

	def execute(self):
		msg = LiveMessage('event-executeaction')
		msg.append({
			'action': self.id
		})
		self.event.manager.live.send(msg)
