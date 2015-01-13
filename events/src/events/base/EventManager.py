# -*- coding: utf-8 -*-

from base import Plugin, implements
from tellduslive.base import TelldusLive, LiveMessage, ITelldusLiveObserver
from telldus import IDeviceChange
from Event import Event
import logging

class EventManager(Plugin):
	implements(ITelldusLiveObserver)
	implements(IDeviceChange)

	def __init__(self):
		self.events = {}
		self.live = TelldusLive(self.context)

	def loadEvent(self, eventId, data):
		event = Event(self, eventId, data['minRepeatInterval'])
		event.loadActions(data['actions'])
		event.loadConditions(data['conditions'])
		event.loadTriggers(data['triggers'])
		self.events[eventId] = event

	@TelldusLive.handler('events-report')
	def receiveEventsFromServer(self, msg):
		data = msg.argument(0).toNative()
		logging.warning("Got event-report")
		logging.warning(str(data))
		for eventId in data:
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

	def stateChanged(self, device, state, statevalue):
		for eid in self.events:
			for tid in self.events[eid].triggers:
				try:
					self.events[eid].triggers[tid].triggerDeviceState(device, state, statevalue)
				except AttributeError as e:
					# The trigger was no DeviceTrigger
					pass
