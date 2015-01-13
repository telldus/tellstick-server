# -*- coding: utf-8 -*-

from base import Plugin, implements, IInterface, ObserverCollection
from tellduslive.base import TelldusLive, LiveMessage, ITelldusLiveObserver
from Event import Event
import logging

class IEventFactory(IInterface):
	def createAction(type, **kwargs):
		"""This method is called when an action is needed"""
	def createCondition(type, **kwargs):
		"""This method is called when a condition is needed"""
	def createTrigger(type, **kwargs):
		"""This method is called when a trigger is needed"""

class EventManager(Plugin):
	implements(ITelldusLiveObserver)

	observers = ObserverCollection(IEventFactory)

	def __init__(self):
		self.events = {}
		self.live = TelldusLive(self.context)

	def loadEvent(self, eventId, data):
		event = Event(self, eventId, data['minRepeatInterval'])
		event.loadActions(data['actions'])
		event.loadConditions(data['conditions'])
		event.loadTriggers(data['triggers'])
		self.events[eventId] = event

	def requestAction(self, type, **kwargs):
		for observer in self.observers:
			action = observer.createAction(type=type, **kwargs)
			if action is not None:
				return action
		return None

	def requestCondition(self, type, **kwargs):
		for observer in self.observers:
			condition = observer.createCondition(type=type, **kwargs)
			if condition is not None:
				return condition
		return None

	def requestTrigger(self, type, **kwargs):
		for observer in self.observers:
			trigger = observer.createTrigger(type=type, **kwargs)
			if trigger is not None:
				return trigger
		return None

	@TelldusLive.handler('events-report')
	def receiveEventsFromServer(self, msg):
		data = msg.argument(0).toNative()
		for eventId in data:
			if eventId not in self.events:
				self.loadEvent(eventId, data[eventId])

	@TelldusLive.handler('event-conditionresult')
	def receiveConditionResultFromServer(self, msg):
		data = msg.argument(0).toNative()
		for eid in self.events:
			event = self.events[eid]
			for cgid in event.conditions:
				cg = event.conditions[cgid]
				for cid in cg.conditions:
					if cid == data['condition']:
						try:
							cg.conditions[cid].receivedResultFromServer(data['status'])
						except AttributeError:
							# Not a RemoteCondition
							pass
						return
