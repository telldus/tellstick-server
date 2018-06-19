# -*- coding: utf-8 -*-

import logging
from threading import Timer
import time

from base import Application, mainthread, Settings
from tellduslive.base import LiveMessage

class Action(object):
	# pylint: disable=W0622
	def __init__(self, event, id, delay, delayPolicy, delayExecTime=None, *__args, **__kwargs):
		super(Action, self).__init__()
		self.event = event
		self.id = id  # pylint: disable=C0103
		self.delay = delay
		self.delayPolicy = delayPolicy
		self.delayExecTime = None
		if delayExecTime:
			self.delayExecTime = float(delayExecTime)
		self.timeout = None
		self.triggerInfo = None
		self.settings = Settings('telldus.event')
		Application().registerShutdown(self.stop)

	def close(self):
		if self.timeout:
			self.timeout.cancel()

	def compareStoredDelay(self, storedActions):
		if not storedActions or str(self.id) not in storedActions:
			return
		storedAction = storedActions[str(self.id)]
		if 'delayExecTime' not in storedAction \
		   or storedAction['delay'] != self.delay \
		   or storedAction['delayPolicy'] != self.delayPolicy:
			return
		# action is waiting for a delay, and delaytime or delaypolicy hasn't been changed,
		# so readd this delay
		self.triggerInfo = None
		if 'triggerInfo' in storedAction:
			self.triggerInfo = storedAction['triggerInfo']
		self.delayExecTime = float(storedAction['delayExecTime'])
		if self.delayExecTime < (time.time() - 900):
			# to late to execute this delayed action now, just ignore it
			self.delayExecTime = None
			self.triggerInfo = None
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

	def execute(self, triggerInfo={}):  # pylint: disable=W0102
		pass

	def executeDelayed(self):
		self.delayExecTime = None
		triggerInfo = self.triggerInfo
		self.triggerInfo = None
		self.updateStoredAction()
		self.execute(triggerInfo)

	def loadParams(self, params):
		for param in params:
			try:
				self.parseParam(param, params[param])
			except Exception as error:
				logging.error(str(error))
				logging.error("Could not parse action param, %s - %s", param, params[param])

	def parseParam(self, name, value):
		pass

	def start(self, triggerInfo=None):
		triggerInfo = triggerInfo or {}
		if self.delay == 0:
			self.execute(triggerInfo)
			return
		else:
			if self.delayPolicy == "continue" and self.delayExecTime:
				# already waiting for this action, do nothing
				return
		if self.timeout:
			self.timeout.cancel()
		self.triggerInfo = triggerInfo
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
		storeddata = self.settings.get('events', {})
		eventId = str(self.event.eventId)
		if eventId in storeddata:
			if 'actions' in storeddata[eventId]:
				actions = storeddata[eventId]['actions']
				if str(self.id) in actions:
					action = actions[str(self.id)]
					if self.delayExecTime:
						action['delayExecTime'] = self.delayExecTime
						action['triggerInfo'] = self.triggerInfo
					else:
						try:
							del action['delayExecTime']
							del action['triggerInfo']
						except Exception as __e:
							pass
		self.settings['events'] = storeddata

class RemoteAction(Action):
	def __init__(self, **kwargs):
		super(RemoteAction, self).__init__(**kwargs)

	def execute(self, triggerInfo=None):
		triggerInfo = triggerInfo or {}
		msg = LiveMessage('event-executeaction')
		msg.append({
			'action': self.id,
			'triggerInfo': triggerInfo
		})
		self.event.manager.live.send(msg)
