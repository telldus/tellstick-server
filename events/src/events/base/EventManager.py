# -*- coding: utf-8 -*-

from base import Plugin, implements, IInterface, mainthread, ObserverCollection, Settings
from tellduslive.base import TelldusLive, LiveMessage, ITelldusLiveObserver
from Event import Event
from UrlAction import UrlAction
import logging

class IEventFactory(IInterface):
	def clearAll():
		"""This method is called to clean up all existing events"""
	def createAction(type, **kwargs):
		"""This method is called when an action is needed"""
	def createCondition(type, **kwargs):
		"""This method is called when a condition is needed"""
	def createTrigger(type, **kwargs):
		"""This method is called when a trigger is needed"""
	def deleteEventTriggers(eventId):
		"""This method is called when an event is deleted"""
	def deleteTrigger(id):
		"""This method is called when a single trigger is deleted"""

class EventManager(Plugin):
	implements(ITelldusLiveObserver)

	observers = ObserverCollection(IEventFactory)

	def __init__(self):
		self.events = {}
		self.s = Settings('telldus.event')
		self.live = TelldusLive(self.context)
		self.loadLocalEvents()

	def loadEvent(self, eventId, data):
		event = Event(self, eventId, data['minRepeatInterval'])
		event.loadActions(data['actions'])
		event.loadConditions(data['conditions'])
		event.loadTriggers(data['triggers'])
		self.events[eventId] = event

	@mainthread
	def loadLocalEvents(self):
		if len(self.events) == 0:
			# only load local events if no report has been received (highly improbable though)
			data = self.s.get('events', {})
			for eventId in data:
				if eventId not in self.events and data[eventId] != "":
					self.loadEvent(eventId, data[eventId])

	def requestAction(self, type, **kwargs):
		for observer in self.observers:
			if type == 'url':
				return UrlAction(type=type, **kwargs)
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
		self.s['events'] = data
		self.events = {}
		for observer in self.observers:
			observer.clearAll()
			for eventId in data:
				if eventId not in self.events:
					self.loadEvent(eventId, data[eventId])

	@TelldusLive.handler('one-event-deleted')
	def receiveDeletedEventFromServer(self, msg):
		eventId = msg.argument(0).toNative()['eventId']
		for observer in self.observers:
			observer.deleteEventTriggers(eventId)
		del self.events[eventId]
		storeddata = self.s.get('events', {})
		storeddata[eventId] = ""
		self.s['events'] = storeddata

	@TelldusLive.handler('one-event-report')
	def receiveEventFromServer(self, msg):
		data = msg.argument(0).toNative()
		eventId = data['eventId']
		for observer in self.observers:
			observer.deleteEventTriggers(eventId)
		if eventId in self.events:
			del self.events[eventId]
		self.loadEvent(eventId, data)
		storeddata = self.s.get('events', {})
		storeddata[eventId] = data
		self.s['events'] = storeddata

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
