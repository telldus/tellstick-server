# -*- coding: utf-8 -*-

from Action import Action
from Condition import Condition
from ConditionContext import ConditionContext
from ConditionGroup import ConditionGroup
from Trigger import Trigger
from threading import Timer
import time
import logging

class Event(object):
	def __init__(self, manager, eventId, minimumRepeatInterval):
		self.manager = manager
		self.eventId = eventId
		self.minimumRepeatInterval = minimumRepeatInterval
		self.lastRun = None
		self.actions = {}
		self.conditions = {}
		self.triggers = {}
		self.evaluatingConditions = []

	def loadActions(self, data):
		for id in data:
			action = Action.load(event=self, id=id, **data[id])
			if not action:
				continue
			if 'params' in data[id]:
				action.loadParams(data[id]['params'])
			self.actions[id] = action

	def loadConditions(self, data):
		for id in data:
			condition = Condition.load(event=self, id=id, **data[id])
			if not condition:
				continue
			if 'params' in data[id]:
				condition.loadParams(data[id]['params'])
			group = data[id]['group'] if 'group' in data[id] else 0
			if group not in self.conditions:
				self.conditions[group] = ConditionGroup()
			self.conditions[group].addCondition(condition)

	def loadTriggers(self, data):
		for id in data:
			trigger = Trigger.load(event=self, id=id, **data[id])
			if not trigger:
				continue
			if 'params' in data[id]:
				trigger.loadParams(data[id]['params'])
			self.triggers[id] = trigger

	def execute(self, trigger):
		self.manager.live.pushToWeb('event', 'trigger', {'event': self.eventId,'trigger': trigger.id})
		if (self.lastRun is not None) and (time.time() - self.lastRun < self.minimumRepeatInterval):
			return
		try:
			if len(self.conditions) == 0:
				# No conditions
				self.__execute()
			else:
				c = ConditionContext(self, self.conditions, success=self.__execute, failure=self.__failure)
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

	def __execute(self):
		# Clear all pending contexts
		self.evaluatingConditions = []
		self.lastRun = time.time()
		self.manager.live.pushToWeb('event', 'update', {'event': self.eventId, 'suspended': self.minimumRepeatInterval})
		for id in self.actions:
			try:
				self.actions[id].start()
				self.manager.live.pushToWeb('event', 'action', {'event': self.eventId, 'action': id})
			except Exception as e:
				logging.error("Could not execute action due to: %s" % str(e))

	def __failure(self):
		self.__cleanContexts()
		if len(self.evaluatingConditions) > 0:
			# Start next context
			self.evaluatingConditions[0].evaluate()
