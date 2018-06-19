# -*- coding: utf-8 -*-

import logging
import time

from base import mainthread
from .Action import RemoteAction
from .Condition import RemoteCondition
from .ConditionContext import ConditionContext
from .ConditionGroup import ConditionGroup

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

	def close(self):
		"""Should always be called when deleting an event"""
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
		for actionId in data:
			action = self.manager.requestAction(event=self, id=int(actionId), **data[actionId])
			if not action:
				action = RemoteAction(event=self, id=int(actionId), **data[actionId])
			if 'params' in data[actionId]:
				action.loadParams(data[actionId]['params'])
			action.compareStoredDelay(storedActions)
			self.actions[int(actionId)] = action

	def loadConditions(self, data):
		for conditionId in data:
			condition = self.manager.requestCondition(event=self, id=conditionId, **data[conditionId])
			if not condition:
				condition = RemoteCondition(event=self, id=conditionId, **data[conditionId])
			if 'params' in data[conditionId]:
				condition.loadParams(data[conditionId]['params'])
			group = data[conditionId]['group'] if 'group' in data[conditionId] else 0
			if group not in self.conditions:
				self.conditions[group] = ConditionGroup()
			self.conditions[group].addCondition(condition)

	def loadTriggers(self, data):
		for triggerId in data:
			trigger = self.manager.requestTrigger(event=self, id=triggerId, **data[triggerId])
			if not trigger:
				continue
			if 'params' in data[triggerId]:
				trigger.loadParams(data[triggerId]['params'])
			self.triggers[triggerId] = trigger

	@mainthread
	def execute(self, trigger, triggerInfo=None):
		triggerInfo = triggerInfo or {}
		self.manager.live.pushToWeb('event', 'trigger', {'event': self.eventId, 'trigger': trigger.id})
		if (self.lastRun is not None) and (time.time() - self.lastRun < self.minimumRepeatInterval):
			return
		try:
			if len(self.conditions) == 0:
				# No conditions
				self.__execute(triggerInfo)
			else:
				conditionContext = ConditionContext(
					self,
					self.conditions,
					success=self.__execute,
					failure=self.__failure,
					triggerInfo=triggerInfo
				)
				self.__cleanContexts()
				if len(self.evaluatingConditions) == 0:
					conditionContext.evaluate()
				self.evaluatingConditions.append(conditionContext)
		except Exception as error:
			logging.warning(str(error))


	def __cleanContexts(self):
		# Clean contexts
		self.evaluatingConditions[:] = [
			x for x in self.evaluatingConditions if x.state is not ConditionContext.DONE
		]

	def __execute(self, triggerInfo=None):
		triggerInfo = triggerInfo or {}
		# Clear all pending contexts
		self.evaluatingConditions = []
		self.lastRun = time.time()
		self.manager.live.pushToWeb('event', 'update', {
			'event': self.eventId,
			'suspended': self.minimumRepeatInterval
		})
		for actionId in self.actions:
			try:
				self.actions[actionId].start(triggerInfo)
				self.manager.live.pushToWeb('event', 'action', {'event': self.eventId, 'action': actionId})
			except Exception as error:
				logging.error("Could not execute action due to: %s", str(error))

	def __failure(self):
		self.__cleanContexts()
		if len(self.evaluatingConditions) > 0:
			# Start next context
			self.evaluatingConditions[0].evaluate()
