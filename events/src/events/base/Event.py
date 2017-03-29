# -*- coding: utf-8 -*-

from base import mainthread, Settings
from Action import Action, RemoteAction
from Condition import Condition, RemoteCondition
from ConditionContext import ConditionContext
from ConditionGroup import ConditionGroup
from Trigger import Trigger
import time
import logging

class Event(object):
	def __init__(self, manager, eventId, minimumRepeatInterval, description):
		self.manager = manager
		self.eventId = eventId
		self.minimumRepeatInterval = minimumRepeatInterval
		self.description = description
		self.lastRun = None
		self.actions = {}
		self.conditions = {}
		self.triggers = {}
		self.evaluatingConditions = []
		self.s = Settings('telldus.event')

	""" Should always be called when deleting an event """
	def close(self):
		for triggerId in self.triggers:
			self.triggers[triggerId].close()
		for actionId in self.actions:
			self.actions[actionId].close()

	def loadActions(self, data, storeddata):
		# check for running action delays
		storedActions = None
		if str(self.eventId) in storeddata:
			if 'actions' in storeddata[str(self.eventId)]:
				storedActions = storeddata[str(self.eventId)]['actions']
		for id in data:
			action = self.manager.requestAction(event=self, id=int(id), **data[id])
			if not action:
				action = RemoteAction(event=self, id=int(id), **data[id])
			if 'params' in data[id]:
				action.loadParams(data[id]['params'])
			action.compareStoredDelay(storedActions)
			self.actions[int(id)] = action

	def loadConditions(self, data):
		for id in data:
			condition = self.manager.requestCondition(event=self, id=id, **data[id])
			if not condition:
				condition = RemoteCondition(event=self, id=id, **data[id])
			if 'params' in data[id]:
				condition.loadParams(data[id]['params'])
			group = data[id]['group'] if 'group' in data[id] else 0
			if group not in self.conditions:
				self.conditions[group] = ConditionGroup()
			self.conditions[group].addCondition(condition)

	def loadTriggers(self, data):
		for id in data:
			trigger = self.manager.requestTrigger(event=self, id=id, **data[id])
			if not trigger:
				continue
			if 'params' in data[id]:
				trigger.loadParams(data[id]['params'])
			self.triggers[id] = trigger

	@mainthread
	def execute(self, trigger, triggerInfo={}):
		self.manager.live.pushToWeb('event', 'trigger', {'event': self.eventId,'trigger': trigger.id})
		if (self.lastRun is not None) and (time.time() - self.lastRun < self.minimumRepeatInterval):
			return
		try:
			if len(self.conditions) == 0:
				# No conditions
				self.__execute(triggerInfo)
			else:
				c = ConditionContext(self, self.conditions, success=self.__execute, failure=self.__failure, triggerInfo=triggerInfo)
				self.__cleanContexts()
				if len(self.evaluatingConditions) == 0:
					c.evaluate()
				self.evaluatingConditions.append(c)
		except Exception as e:
			logging.warning(str(e))


	def __cleanContexts(self):
		i = len(self.evaluatingConditions)
		# Clean contexts
		self.evaluatingConditions[:] = [x for x in self.evaluatingConditions if x.state is not ConditionContext.DONE]

	def __execute(self, triggerInfo={}):
		# Clear all pending contexts
		self.evaluatingConditions = []
		self.lastRun = time.time()
		self.manager.live.pushToWeb('event', 'update', {'event': self.eventId, 'suspended': self.minimumRepeatInterval})
		for id in self.actions:
			try:
				self.actions[id].start(triggerInfo)
				self.manager.live.pushToWeb('event', 'action', {'event': self.eventId, 'action': id})
			except Exception as e:
				logging.error("Could not execute action due to: %s" % str(e))

	def __failure(self):
		self.__cleanContexts()
		if len(self.evaluatingConditions) > 0:
			# Start next context
			self.evaluatingConditions[0].evaluate()
