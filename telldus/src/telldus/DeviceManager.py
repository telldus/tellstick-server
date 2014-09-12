# -*- coding: utf-8 -*-

import json
from tellduslive.base import TelldusLive, LiveMessage, LiveMessageToken, ITelldusLiveObserver
from base import Settings, Plugin, implements
import time

class DeviceManager(Plugin):
	implements(ITelldusLiveObserver)

	def __init__(self):
		self.devices = []
		self.s = Settings('telldus.devicemanager')
		self.nextId = self.s.get('nextId', 0)
		self.live = TelldusLive(self.context)
		self.registered = False
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
		if self.live.registered:
			deviceDict = {
				'id': device.id(),
				'name': device.name(),
				'methods': device.methods(),
				'state': 2,
				'stateValue': '',
				'transport': device.typeString()
			}
			msg = LiveMessage("DeviceAdded")
			msg.append(deviceDict)
			self.live.send(msg)

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
		if self.live.registered:
			msg = LiveMessage("DeviceRemoved")
			msg.append({'id': deviceId})
			self.live.send(msg)

	def sensorValueUpdated(self, device):
		if not self.live.registered:
			return
		if device.isSensor() == False:
			return
		msg = LiveMessage("SensorEvent")
		sensor = {
			'name': device.name(),
			'protocol': 'z-wave',
			'model': 'n/a',
			'sensor_id': device.id(),
		}
		msg.append(sensor)
		values = device.sensorValues()
		valueList = []
		for valueType in values:
			valueList.append({
				'type': valueType,
				'lastUp': str(int(time.time())),
				'value': str(values[valueType])
			})
		msg.append(valueList)
		self.live.send(msg)

	def stateUpdated(self, device):
		if not self.live.registered:
			return
		if device.isDevice() == False:
			return
		(state, stateValue) = device.state()
		msg = LiveMessage("DeviceEvent")
		msg.append(device.id())
		msg.append(state)
		msg.append(stateValue)
		self.live.send(msg)

	@TelldusLive.handler('command')
	def __handleCommand(self, msg):
		args = msg.argument(0).dictVal
		action = args['action'].stringVal
		id = args['id'].intVal
		for dev in self.devices:
			if dev.id() != id:
				continue
			dev.command(action)

	@TelldusLive.handler('device')
	def __handleDeviceCommand(self, msg):
		args = msg.argument(0).dictVal
		if 'action' not in args:
			return
		if args['action'].stringVal == 'setName':
			if 'name' not in args or args['name'].stringVal == '':
				return
			for dev in self.devices:
				if dev.id() != args['device'].intVal:
					continue
				dev.setName(args['name'].stringVal)
				self.__sendDeviceReport()
				break

	def liveRegistered(self, params):
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
				'transport': d.typeString()
			}
			l.append(device)
		msg = LiveMessage("DevicesReport")
		msg.append(l)
		self.live.send(msg)

	def __sendSensorReport(self):
		if not self.live.registered:
			return
		l = []
		for d in self.devices:
			if d.isSensor() == False:
				continue
			sensorFrame = []
			sensor = {
				'name': d.name(),
				'protocol': 'z-wave',
				'model': 'n/a',
				'sensor_id': d.id(),
			}
			sensorFrame.append(sensor)
			valueList = []
			# TODO(micke): Add current values
			sensorFrame.append(valueList)
			l.append(sensorFrame)
		msg = LiveMessage("SensorsReport")
		msg.append(l)
		self.live.send(msg)

