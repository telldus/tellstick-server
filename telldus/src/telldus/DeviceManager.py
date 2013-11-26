# -*- coding: utf-8 -*-

import json
from tellduslive.base import TelldusLive, LiveMessage
from base import Settings

class DeviceManager(object):
	def __init__(self,):
		super(DeviceManager,self).__init__()
		self.devices = []
		self.s = Settings('telldus.devicemanager')
		self.nextId = self.s.get('nextId', 0)
		self.live = TelldusLive()
		self.registered = False
		self.live.registerHandler('registered', self.__liveRegistered)
		self.live.registerHandler('command', self.__handleCommand)
		self.__load()

	def addDevice(self, device):
		self.devices.append(device)
		device.setManager(self)
		# Find out if this one was saved before
		found = False
		for i, dev in enumerate(self.store):
			if 'type' not in dev or 'localId' not in dev:
				continue
			if dev['type'] == device.typeString() and dev['localId'] == device.localId():
				device.load(dev)
				del self.store[i]
				found = True
				break
		if not found:
			self.nextId = self.nextId + 1
			device.setId(self.nextId)
		self.save()
		self.__sendDeviceReport()

	def device(self, deviceId):
		for d in self.devices:
			if d.id() == deviceId:
				return d
		return None

	def removeDevice(self, deviceId):
		print("Trying to remove device", deviceId)
		for i, device in enumerate(self.devices):
			if device.id() == deviceId:
				print("Found it")
				del self.devices[i]
				break
		self.save()
		self.__sendDeviceReport()

	def stateUpdated(self, device):
		if not self.live.registered:
			return
		(state, stateValue) = device.state()
		msg = LiveMessage("DeviceEvent")
		msg.append(device.id())
		msg.append(state)
		msg.append(stateValue)
		self.live.send(msg)

	def __handleCommand(self, msg):
		args = msg.argument(0).dictVal
		action = args['action'].stringVal
		id = args['id'].intVal
		for dev in self.devices:
			if dev.id() != id:
				continue
			dev.command(action)

	def __liveRegistered(self, msg):
		self.registered = True
		self.__sendDeviceReport()

	def __load(self):
		self.store = self.s.get('devices', [])

	def save(self):
		data = []
		for d in self.devices:
			data.append({
				"id": d.id(),
				"localId": d.localId(),
				"type": d.typeString(),
				"name": d.name(),
				"params": d.params(),
			})
		self.s['devices'] = data
		self.s['nextId'] = self.nextId

	def __sendDeviceReport(self):
		if not self.live.registered:
			return
		l = []
		for d in self.devices:
			device = {
				'id': d.id(),
				'name': d.name(),
				'methods': d.methods(),
				'state': 2,
				'stateValue': '',
			}
			l.append(device)
		msg = LiveMessage("DevicesReport")
		msg.append(l)
		self.live.send(msg)

