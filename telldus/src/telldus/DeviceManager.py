# -*- coding: utf-8 -*-

from Device import CachedDevice, DeviceAbortException
import json
from tellduslive.base import TelldusLive, LiveMessage, LiveMessageToken, ITelldusLiveObserver
from base import Settings, ObserverCollection, IInterface, Plugin, implements
import time

class IDeviceChange(IInterface):
	def deviceAdded(device):
		"""This method is called when a device is added"""
	def deviceConfirmed(device):
		"""This method is called when a device is confirmed on the network, not only loaded from storage (not applicable to all device types)"""
	def deviceRemoved(deviceId):
		"""This method is called when a device is removed"""
	def stateChanged(device, state, statevalue):
		"""Called when the state of a device changed"""

class DeviceManager(Plugin):
	implements(ITelldusLiveObserver)

	observers = ObserverCollection(IDeviceChange)

	def __init__(self):
		self.devices = []
		self.s = Settings('telldus.devicemanager')
		self.nextId = self.s.get('nextId', 0)
		self.live = TelldusLive(self.context)
		self.registered = False
		self.__load()

	def addDevice(self, device):
		cachedDevice = None
		for i, delDevice in enumerate(self.devices):
			# Delete the cached device from loaded devices, since it is replaced by a confirmed/specialised one
			if delDevice.localId() == device.localId() and device.typeString() == delDevice.typeString() and not delDevice.confirmed():
				cachedDevice = delDevice
				del self.devices[i]
				break
		self.devices.append(device)
		device.setManager(self)

		if not cachedDevice:  # New device, not stored in local cache
			self.nextId = self.nextId + 1
			device.setId(self.nextId)
		else:  # Transfer parameters from the loaded one
			device.loadCached(cachedDevice)
		self.save()
		
		if not cachedDevice:
			self.observers.deviceAdded(device)
			if self.live.registered and device.isDevice():
				(state, stateValue) = device.state()
				deviceDict = {
					'id': device.id(),
					'name': device.name(),
					'methods': device.methods(),
					'state': state,
					'stateValue': stateValue,
					'transport': device.typeString()
				}
				msg = LiveMessage("DeviceAdded")
				msg.append(deviceDict)
				self.live.send(msg)
		else:
			# Previously cached device is now confirmed, TODO notify Live! about this too?
			self.observers.deviceConfirmed(device)

	def device(self, deviceId):
		for d in self.devices:
			if d.id() == deviceId:
				return d
		return None

	def finishedLoading(self, type):
		""" Finished loading all devices of this type. If there are any unconfirmed, these should be deleted """
		for device in self.devices:
			if device.typeString() == type and not device.confirmed():
				self.removeDevice(device.id())

	def removeDevice(self, deviceId):
		isDevice = True
		for i, device in enumerate(self.devices):
			if device.id() == deviceId:
				self.observers.deviceRemoved(deviceId)
				isDevice = self.devices[i].isDevice()
				del self.devices[i]
				break
		self.save()
		if self.live.registered and isDevice:
			msg = LiveMessage("DeviceRemoved")
			msg.append({'id': deviceId})
			self.live.send(msg)

	def retrieveDevices(self, deviceType = None):
		l = []
		for d in self.devices:
			if deviceType is not None and d.typeString() != deviceType:
				continue
			l.append(d)
		return l

	def sensorValueUpdated(self, device):
		if not self.live.registered:
			return
		if device.isSensor() == False:
			return
		msg = LiveMessage("SensorEvent")
		sensor = {
			'name': device.name(),
			'protocol': device.typeString(),
			'model': 'n/a',
			'sensor_id': device.id(),
		}
		msg.append(sensor)
		values = device.sensorValues()
		valueList = []
		for valueType in values:
			for value in values[valueType]:
				print value
				valueList.append({
					'type': valueType,
					'lastUp': str(int(time.time())),
					'value': str(value['value']),
					'scale': value['scale']
				})
		msg.append(valueList)
		self.live.send(msg)

	def stateUpdated(self, device, ackId = None, origin = None):
		if not self.live.registered:
			return
		if device.isDevice() == False:
			return
		extras = {}
		if ackId:
			extras['ACK'] = ackId
		if origin:
			extras['origin'] = origin
		else:
			extras['origin'] = 'Incoming signal'
		(state, stateValue) = device.state()
		self.observers.stateChanged(device, state, stateValue)
		msg = LiveMessage("DeviceEvent")
		msg.append(device.id())
		msg.append(state)
		msg.append(stateValue)
		msg.append(extras)
		self.live.send(msg)

	def stateUpdatedFail(self, device, state, stateValue, reason, origin):
		if not self.live.registered:
			return
		if device.isDevice() == False:
			return
		extras = {
			'reason': reason,
		}
		if origin:
			extras['origin'] = origin
		else:
			extras['origin'] = 'Unknown'
		(state, stateValue) = device.state()
		self.observers.stateChanged(device, state, stateValue)
		msg = LiveMessage('DeviceFailEvent')
		msg.append(device.id())
		msg.append(state)
		msg.append(stateValue)
		msg.append(extras)
		self.live.send(msg)

	@TelldusLive.handler('command')
	def __handleCommand(self, msg):
		args = msg.argument(0).toNative()
		action = args['action']
		value = args['value'] if 'value' in args else None
		id = args['id']
		device = None
		for dev in self.devices:
			if dev.id() == id:
				device = dev
				break

		def success(state, stateValue):
			if 'ACK' in args:
				device.setState(state, stateValue, ack=args['ACK'])
				# Abort the DeviceEvent this triggered
				raise DeviceAbortException()
		def fail(reason):
			# We failed to set status for some reason, nack the server
			if 'ACK' in args:
				msg = LiveMessage('NACK')
				msg.append({
					'ackid': args['ACK'],
					'reason': reason,
				})
				self.live.send(msg)
				# Abort the DeviceEvent this triggered
				raise DeviceAbortException()

		device.command(action, value, success=success, failure=fail)

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

	def liveRegistered(self, msg):
		self.registered = True
		self.__sendDeviceReport()
		self.__sendSensorReport()

	def __load(self):
		self.store = self.s.get('devices', [])
		for dev in self.store:
			if 'type' not in dev or 'localId' not in dev:
				continue  # This should not be possible
			self.devices.append(CachedDevice(dev))

	def save(self):
		data = []
		for d in self.devices:
			(state, stateValue) = d.state()
			data.append({
				"id": d.id(),
				"localId": d.localId(),
				"type": d.typeString(),
				"name": d.name(),
				"params": d.params(),
				"methods": d.methods(),
				"state": state,
				"stateValue": stateValue
			})
		self.s['devices'] = data
		self.s['nextId'] = self.nextId

	def __sendDeviceReport(self):
		if not self.live.registered:
			return
		l = []
		for d in self.devices:
			if not d.isDevice():
				continue
			(state, stateValue) = d.state()
			device = {
				'id': d.id(),
				'name': d.name(),
				'methods': d.methods(),
				'state': state,
				'stateValue': stateValue,
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
				'protocol': d.typeString(),
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

