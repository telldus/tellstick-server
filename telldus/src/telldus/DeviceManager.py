# -*- coding: utf-8 -*-

from Device import CachedDevice, DeviceAbortException
import json
from tellduslive.base import TelldusLive, LiveMessage, LiveMessageToken, ITelldusLiveObserver
from base import Application, Settings, ObserverCollection, IInterface, Plugin, implements, mainthread, signal
import time

__name__ = 'telldus'

class IDeviceChange(IInterface):
	"""Implement this IInterface to recieve notifications on device changes"""

	def deviceAdded(device):
		"""This method is called when a device is added"""
	def deviceConfirmed(device):
		"""This method is called when a device is confirmed on the network, not only loaded from storage (not applicable to all device types)"""
	def deviceRemoved(deviceId):
		"""This method is called when a device is removed"""
	def sensorValueUpdated(device, valueType, value, scale):
		"""This method is called when a new sensor value is received from a sensor"""
	def stateChanged(device, state, statevalue):
		"""Called when the state of a device changed"""

class DeviceManager(Plugin):
	"""The devicemanager holds and manages all the devices in the server"""
	implements(ITelldusLiveObserver)

	observers = ObserverCollection(IDeviceChange)

	def __init__(self):
		self.devices = []
		self.s = Settings('telldus.devicemanager')
		self.nextId = self.s.get('nextId', 0)
		self.live = TelldusLive(self.context)
		self.registered = False
		self.__load()

	@mainthread
	def addDevice(self, device):
		"""Call this function to register a new device to the device manager.

		.. note::
		    The :func:`localId` function in the device must return a unique id for
		    the transport type returned by :func:`typeString`
		"""
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
			self.__deviceAdded(device)
			if self.live.registered and device.isDevice():
				(state, stateValue) = device.state()
				deviceDict = {
					'id': device.id(),
					'name': device.name(),
					'methods': device.methods(),
					'state': state,
					'stateValue': stateValue,
					'protocol': device.protocol(),
					'model': device.model(),
					'transport': device.typeString()
				}
				msg = LiveMessage("DeviceAdded")
				msg.append(deviceDict)
				self.live.send(msg)
		else:
			# Previously cached device is now confirmed, TODO notify Live! about this too?
			self.observers.deviceConfirmed(device)

	def device(self, deviceId):
		"""Retrieves a device.

		Returns:
		  the device specified by `deviceId` or None of no device was found
		"""
		for d in self.devices:
			if d.id() == deviceId:
				return d
		return None

	def findByName(self, name):
		for d in self.devices:
			if d.name() == name:
				return d
		return None

	@mainthread
	def finishedLoading(self, type):
		""" Finished loading all devices of this type. If there are any unconfirmed, these should be deleted """
		for device in self.devices:
			if device.typeString() == type and not device.confirmed():
				self.removeDevice(device.id())

	@mainthread
	def removeDevice(self, deviceId):
		"""Removes a device.

		.. warning::
		    This function may only be called by the module supplying the device
		    since removing of a device may be transport specific.
		"""
		isDevice = True
		for i, device in enumerate(self.devices):
			if device.id() == deviceId:
				self.__deviceRemoved(deviceId)
				isDevice = self.devices[i].isDevice()
				del self.devices[i]
				break
		self.save()
		if self.live.registered and isDevice:
			msg = LiveMessage("DeviceRemoved")
			msg.append({'id': deviceId})
			self.live.send(msg)

	def retrieveDevices(self, deviceType = None):
		"""Retrieve a list of devices.

		Args:
		    :deviceType: If this parameter is set only devices with this type is returned

		Returns:
		    Returns a list of devices
		"""
		l = []
		for d in self.devices:
			if deviceType is not None and d.typeString() != deviceType:
				continue
			l.append(d)
		return l

	@signal
	def sensorValueUpdated(self, device, valueType, value, scale):
		"""
		Called every time a sensors value is updated.
		"""
		if device.isSensor() == False:
			return
		self.observers.sensorValueUpdated(device, valueType, value, scale)
		if not self.live.registered or device.ignored():
			# don't send if not connected to live or sensor is ignored
			return
		if valueType in device.lastUpdatedLive and (valueType in device.valueChangedTime and device.valueChangedTime[valueType] < device.lastUpdatedLive[valueType]) and device.lastUpdatedLive[valueType] > (int(time.time()) - 300):
			# no values have changed since the last live-update, and the last time this sensor was sent to live was less than 5 minutes ago
			return

		msg = LiveMessage("SensorEvent")
		sensor = {
			'name': device.name(),
			'protocol': device.protocol(),
			'model': device.model(),
			'sensor_id': device.id(),
		}
		battery = device.battery()
		if battery is not None:
			sensor['battery'] = battery
		msg.append(sensor)
		# small clarification: valueType etc that is sent in here is only used for sending
		# information about what have changed on to observers, below is instead all the values
		# of the sensor picked up and sent in a sensor event-message (the sensor values
		# have already been updated in other words)
		values = device.sensorValues()
		valueList = []
		for vt in values:
			for value in values[vt]:
				valueList.append({
					'type': vt,
					'lastUp': str(value['lastUpdated']),
					'value': str(value['value']),
					'scale': value['scale']
				})
		msg.append(valueList)
		device.lastUpdatedLive[valueType] = int(time.time())
		self.live.send(msg)

	def stateUpdated(self, device, ackId = None, origin = None):
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
		self.__deviceStateChanged(device, state, stateValue)
		self.save()
		if not self.live.registered:
			return
		msg = LiveMessage("DeviceEvent")
		msg.append(device.id())
		msg.append(state)
		msg.append(str(stateValue))
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
		self.__deviceStateChanged(device, state, stateValue)
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
		args = msg.argument(0).toNative()
		if 'action' not in args:
			return
		if args['action'] == 'setName':
			if 'name' not in args or args['name'] == '':
				return
			for dev in self.devices:
				if dev.id() != args['device']:
					continue
				if type(args['name']) is int:
					dev.setName(str(args['name']))
				else:
					dev.setName(args['name'].decode('UTF-8'))
				if dev.isDevice():
					self.__sendDeviceReport()
				if dev.isSensor:
					self.__sendSensorReport()
				return

	@TelldusLive.handler('reload')
	def __handleSensorUpdate(self, msg):
		reloadType = msg.argument(0).toNative()
		if reloadType != 'sensor':
			# not for us
			return
		data = msg.argument(1).toNative()
		if not msg.argument(2) or 'sensorId' not in msg.argument(2).toNative():
			# nothing to do, might be an orphaned zwave sensor
			return
		sensorId = msg.argument(2).toNative()['sensorId']
		updateType = data['type']
		for dev in self.devices:
			if dev.id() == sensorId:
				if updateType == 'updateignored':
					value = data['ignored']
					if dev.ignored() == value:
						return
					dev.setIgnored(value)
				self.__sendSensorChange(sensorId, updateType, value)
				return

	def liveRegistered(self, msg):
		self.registered = True
		self.__sendDeviceReport()
		self.__sendSensorReport()

	def __load(self):
		self.store = self.s.get('devices', [])
		for dev in self.store:
			if 'type' not in dev or 'localId' not in dev:
				continue  # This should not be possible
			d = CachedDevice(dev)
			# If we have loaded this device from cache 5 times in a row it's
			# considered dead
			if d.loadCount() < 5:
				self.devices.append(d)

	@signal('deviceAdded')
	def __deviceAdded(self, device):
		"""
		Called every time a device is added/created
		"""
		self.observers.deviceAdded(device)

	@signal('deviceRemoved')
	def __deviceRemoved(self, deviceId):
		"""
		Called every time a device is removed. The parameter deviceId is the old
		device id. The ref to the device is no longer available
		"""
		self.observers.deviceRemoved(deviceId)

	@signal('deviceStateChanged')
	def __deviceStateChanged(self, device, state, stateValue):
		"""
		Called every time the state of a device is changed.
		"""
		self.observers.stateChanged(device, state, stateValue)

	def save(self):
		data = []
		for d in self.devices:
			(state, stateValue) = d.state()
			dev = {
				"id": d.id(),
				"loadCount": d.loadCount(),
				"localId": d.localId(),
				"type": d.typeString(),
				"name": d.name(),
				"params": d.params(),
				"methods": d.methods(),
				"state": state,
				"stateValue": stateValue,
				"ignored": d.ignored()
			}
			if len(d.sensorValues()) > 0:
				dev['sensorValues'] = d.sensorValues()
			data.append(dev)
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
				'protocol': d.protocol(),
				'model': d.model(),
				'transport': d.typeString(),
				'ignored': d.ignored()
			}
			battery = d.battery()
			if battery is not None:
				device['battery'] = battery
			l.append(device)
		msg = LiveMessage("DevicesReport")
		msg.append(l)
		self.live.send(msg)

	def __sendSensorChange(self, sensorid, valueType, value):
		msg = LiveMessage("SensorChange")
		device = None
		for d in self.devices:
			if d.id() == sensorid:
				device = d
				break
		if not device:
			return
		sensor = {
			'protocol': device.typeString(),
			'model': device.model(),
			'sensor_id': device.id(),
		}
		msg.append(sensor)
		msg.append(valueType)
		msg.append(value)
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
				'protocol': d.protocol(),
				'model': d.model(),
				'sensor_id': d.id(),
			}
			battery = d.battery()
			if battery is not None:
				sensor['battery'] = battery
			sensorFrame.append(sensor)
			valueList = []
			values = d.sensorValues()
			for valueType in values:
				for value in values[valueType]:
					valueList.append({
						'type': valueType,
						'lastUp': str(value['lastUpdated']),
						'value': str(value['value']),
						'scale': value['scale']
					})
					#d.lastUpdatedLive[valueType] = int(time.time())  # Telldus Live! does not aknowledge sensorreportupdates yet, so don't count this yet (wait for Cassandra only)
			sensorFrame.append(valueList)
			l.append(sensorFrame)
		msg = LiveMessage("SensorsReport")
		msg.append(l)
		self.live.send(msg)

	def sensorsUpdated(self):
		self.__sendSensorReport()