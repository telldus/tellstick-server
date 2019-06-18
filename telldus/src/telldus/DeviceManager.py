# -*- coding: utf-8 -*-

import hashlib
import json
import logging
import time
from tellduslive.base import TelldusLive, LiveMessage, ITelldusLiveObserver
from base import \
	Settings, \
	ObserverCollection, \
	IInterface, \
	ISignalObserver, \
	Plugin, \
	implements, \
	mainthread, \
	signal, \
	slot
from .Device import CachedDevice, DeviceAbortException

__name__ = 'telldus'  # pylint: disable=W0622

class IDeviceChange(IInterface):
	"""Implement this IInterface to recieve notifications on device changes

	.. deprecated:: 1.2
	   Use signals/slots instead to avoid hard dependencies
	"""

	def deviceAdded(device):  # pylint: disable=E0213
		"""This method is called when a device is added"""
	def deviceConfirmed(device):  # pylint: disable=E0213
		"""
		This method is called when a device is confirmed on the network,
		not only loaded from storage (not applicable to all device types)
		"""
	def deviceRemoved(deviceId):  # pylint: disable=E0213
		"""This method is called when a device is removed"""
	def deviceUpdated(device, parameters):  #pylint: disable=E0213
		"""This method is called when device parameters is updated"""
	def sensorValueUpdated(device, valueType, value, scale):  # pylint: disable=E0213
		"""This method is called when a new sensor value is received from a sensor"""
	def stateChanged(device, state, statevalue):  # pylint: disable=E0213
		"""Called when the state of a device changed"""

class DeviceManager(Plugin):
	"""The devicemanager holds and manages all the devices in the server"""
	implements(ITelldusLiveObserver)

	observers = ObserverCollection(IDeviceChange)

	public = True

	def __init__(self):
		self.devices = []
		self.settings = Settings('telldus.devicemanager')
		self.nextId = self.settings.get('nextId', 0)
		self.live = TelldusLive(self.context)
		self.registered = False
		self.__load()

	@mainthread
	def addDevice(self, device):
		"""
		Call this function to register a new device to the device manager.

		.. note::
		    The :func:`Device.localId() <telldus.Device.localId>` function in the device must return
		    a unique id for the transport type returned by
		    :func:`Device.typeString() <telldus.Device.localId>`
		"""
		cachedDevice = None
		for i, delDevice in enumerate(self.devices):
			# Delete the cached device from loaded devices, since it is replaced
			# by a confirmed/specialised one
			if delDevice.localId() == device.localId() \
			   and device.typeString() == delDevice.typeString() \
			   and not delDevice.confirmed():
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
				parameters = json.dumps(
					device.allParameters(),
					separators=(',', ':'),
					sort_keys=True
				)
				deviceDict = {
					'id': device.id(),
					'name': device.name(),
					'methods': device.methods(),
					'state': state,
					'stateValue': stateValue,
					'stateValues': device.stateValues(),
					'protocol': device.protocol(),
					'model': device.model(),
					'parameters': parameters,
					'parametersHash': hashlib.sha1(parameters).hexdigest(),
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

		:param int deviceId: The id of the device to be returned.
		:returns: the device specified by `deviceId` or None of no device was found
		"""
		for device in self.devices:
			if device.id() == deviceId:
				return device
		return None

	def deviceMetadataUpdated(self, device, param):
		self.save()
		if param and param != '':
			sendParameters = False
			if param == 'devicetype':
				# This effects device parameters also
				sendParameters = True
			self.__sendDeviceParameterReport(device, sendParameters=sendParameters, sendMetadata=True)

	def deviceParamUpdated(self, device, param):
		self.save()
		self.__deviceUpdated(device, [param])
		if param == 'name':
			if device.isDevice():
				self.__sendDeviceReport()
			if device.isSensor:
				self.__sendSensorReport()
			return
		if param and param != '':
			self.__sendDeviceParameterReport(device, sendParameters=True, sendMetadata=False)

	def findByName(self, name):
		for device in self.devices:
			if device.name() == name:
				return device
		return None

	@mainthread
	def finishedLoading(self, deviceType):
		"""
		Finished loading all devices of this type. If there are any unconfirmed,
		these should be deleted
		"""
		for device in self.devices:
			if device.typeString() == deviceType and not device.confirmed():
				self.removeDevice(device.id())

	@mainthread
	def removeDevice(self, deviceId):
		"""
		Removes a device.

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

	@mainthread
	def removeDevicesByType(self, deviceType):
		"""
		.. versionadded:: 1.1.0

		Remove all devices of a specific device type

		:param str deviceType: The type of devices to remove
		"""
		deviceIds = []
		for device in self.devices:
			if device.typeString() == deviceType:
				deviceIds.append(device.id())
		for deviceId in deviceIds:
			self.removeDevice(deviceId)

	def retrieveDevices(self, deviceType=None):
		"""Retrieve a list of devices.

		:param deviceType: If this parameter is set only devices with this type is returned
		:type deviceType: str or None
		:returns: a list of devices
		"""
		lst = []
		for device in self.devices:
			if deviceType is not None and device.typeString() != deviceType:
				continue
			lst.append(device)
		return lst

	@signal
	def sensorValueUpdated(self, device, valueType, value, scale):
		"""
		Called every time a sensor value is updated.

		:param device: The device/sensor being updated
		:param valueType: Type of updated value
		:param value: The updated value
		:param scale: Scale of updated value
		"""
		pass

	@signal
	def sensorValuesUpdated(self, device, values):
		"""
		Called every time a sensor value is updated.

		:param device: The device/sensor being updated
		:param values: A list with all values updated
		"""
		if device.isSensor() is False:
			return
		shouldUpdateLive = False
		for valueElement in values:
			valueType = valueElement['type']
			value = valueElement['value']
			scale = valueElement['scale']
			self.observers.sensorValueUpdated(device, valueType, value, scale)
			self.sensorValueUpdated(device, valueType, value, scale)
			if valueType not in device.lastUpdatedLive \
			   or valueType not in device.valueChangedTime \
			   or device.valueChangedTime[valueType] > device.lastUpdatedLive[valueType] \
			   or device.lastUpdatedLive[valueType] < (int(time.time()) - 300):
				shouldUpdateLive = True
				break

		if not self.live.registered or device.ignored() or not shouldUpdateLive:
			# don't send if not connected to live, sensor is ignored or if
			# values haven't changed and five minutes hasn't passed yet
			return

		msg = LiveMessage("SensorEvent")
		# pcc = packageCountChecked - already checked package count,
		# just accept it server side directly
		sensor = {
			'name': device.name(),
			'protocol': device.protocol(),
			'model': device.model(),
			'sensor_id': device.id(),
			'pcc': 1,
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
		for valueType in values:
			device.lastUpdatedLive[valueType] = int(time.time())
			for value in values[valueType]:
				valueList.append({
					'type': valueType,
					'lastUp': str(value['lastUpdated']),
					'value': str(value['value']),
					'scale': value['scale']
				})
		msg.append(valueList)
		self.live.send(msg)

	def stateUpdated(self, device, ackId=None, origin=None):
		if device.isDevice() is False:
			return
		extras = {
			'stateValues': device.stateValues()
		}
		if ackId:
			extras['ACK'] = ackId
		if origin:
			extras['origin'] = origin
		else:
			extras['origin'] = 'Incoming signal'
		(state, stateValue) = device.state()
		self.__deviceStateChanged(device, state, stateValue, extras['origin'])
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
		if device.isDevice() is False:
			return
		extras = {
			'reason': reason,
		}
		if origin:
			extras['origin'] = origin
		else:
			extras['origin'] = 'Unknown'
		(state, stateValue) = device.state()
		self.__deviceStateChanged(device, state, stateValue, extras['origin'])
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
		deviceId = args['id']
		device = None
		for dev in self.devices:
			if dev.id() == deviceId:
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
				if isinstance(args['name'], int):
					dev.setName(str(args['name']))
				else:
					dev.setName(args['name'].decode('UTF-8'))
				return
		elif args['action'] in ('setParameter', 'setMetadata'):
			device = None
			for dev in self.devices:
				if dev.id() == args['device']:
					device = dev
					break
			if device is None:
				return
			name = args.get('name', '')
			value = args.get('value', '')
			if args['action'] == 'setParameter':
				if name == 'room':
					device.setRoom(value)
				else:
					device.setParameter(name, value)
			else:
				device.setMetadata(name, value)

	@TelldusLive.handler('device-requestdata')
	def __handleDeviceParametersRequest(self, msg):
		args = msg.argument(0).toNative()
		device = self.device(args.get('id', 0))
		if not device:
			return
		sendParameters = True if args.get('parameters', 0) == 1 else False
		sendMetadata = True if args.get('metadata', 0) == 1 else False
		self.__sendDeviceParameterReport(device, sendParameters, sendMetadata)

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
		if updateType == 'updateignored' and len(self.devices) > 0:
			# we don't have this sensor, do something! (can't send sensor change
			# back (__sendSensorChange), because can't create message when
			# sensor is unknown (could create special workaround, but only do
			# that if it's still a problem in the future))
			logging.warning('Requested ignore change for non-existing sensor %s', str(sensorId))
			# send an updated sensor report, so that this sensor is hopefully
			# cleaned up
			self.__sendSensorReport()

	def liveRegistered(self, __msg, refreshRequired):
		self.registered = True
		self.__sendDeviceReport()
		self.__sendSensorReport()

	def __load(self):
		self.store = self.settings.get('devices', [])
		for dev in self.store:
			if 'type' not in dev or 'localId' not in dev:
				continue  # This should not be possible
			device = CachedDevice(dev)
			# If we have loaded this device from cache 5 times in a row it's
			# considered dead
			if device.loadCount() < 5:
				self.devices.append(device)

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

	@signal('deviceUpdated')
	def __deviceUpdated(self, device, parameters):
		"""
		Called every time a device parameter is updated
		"""
		self.observers.deviceUpdated(device, parameters)

	@signal('deviceStateChanged')
	def __deviceStateChanged(self, device, state, stateValue, origin):
		"""
		Called every time the state of a device is changed.
		"""
		del origin  # Remove pylint warning
		self.observers.stateChanged(device, state, stateValue)

	def save(self):
		data = []
		for device in self.devices:
			(state, __stateValue) = device.state()
			stateValues = device.stateValues()
			dev = {
				"id": device.id(),
				"loadCount": device.loadCount(),
				"localId": device.localId(),
				"type": device.typeString(),
				"name": device.name(),
				"params": device.params(),
				"metadata": device.metadata(),
				"methods": device.methods(),
				"state": state,
				"stateValues": stateValues,
				"ignored": device.ignored(),
				"isSensor": device.isSensor()
			}
			if len(device.sensorValues()) > 0:
				dev['sensorValues'] = device.sensorValues()
			battery = device.battery()
			if battery is not None:
				dev['battery'] = battery
			if hasattr(device, 'declaredDead') and device.declaredDead:
				dev['declaredDead'] = device.declaredDead
			data.append(dev)
		self.settings['devices'] = data
		self.settings['nextId'] = self.nextId

	def __sendDeviceReport(self):
		logging.warning("Send Devices Report")
		if not self.live.registered:
			return
		lst = []
		for device in self.devices:
			if not device.isDevice():
				continue
			(state, stateValue) = device.state()
			parametersHash = hashlib.sha1(json.dumps(
				device.allParameters(),
				separators=(',', ':'),
				sort_keys=True
			))
			metadataHash = hashlib.sha1(json.dumps(
				device.metadata(),
				separators=(',', ':'),
				sort_keys=True
			))
			dev = {
				'id': device.id(),
				'name': device.name(),
				'methods': device.methods(),
				'state': state,
				'stateValue': str(stateValue),
				'stateValues': device.stateValues(),
				'protocol': device.protocol(),
				'model': device.model(),
				'parametersHash': parametersHash.hexdigest(),
				'metadataHash': metadataHash.hexdigest(),
				'transport': device.typeString(),
				'ignored': device.ignored()
			}
			battery = device.battery()
			if battery is not None:
				dev['battery'] = battery
			lst.append(dev)
		msg = LiveMessage("DevicesReport")
		msg.append(lst)
		self.live.send(msg)

	def __sendSensorChange(self, sensorid, valueType, value):
		msg = LiveMessage("SensorChange")
		device = None
		for dev in self.devices:
			if dev.id() == sensorid:
				device = dev
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

	def __sendDeviceParameterReport(self, device, sendParameters, sendMetadata):
		reply = LiveMessage('device-datareport')
		data = {
			'id': device.id()
		}
		if sendParameters:
			parameters = json.dumps(
				device.allParameters(),
				separators=(',', ':'),
				sort_keys=True
			)
			data['parameters'] = parameters
			data['parametersHash'] = hashlib.sha1(parameters).hexdigest()
		if sendMetadata:
			metadata = json.dumps(
				device.metadata(),
				separators=(',', ':'),
				sort_keys=True
			)
			data['metadata'] = metadata
			data['metadataHash'] = hashlib.sha1(metadata).hexdigest()
		reply.append(data)
		self.live.send(reply)

	def __sendSensorReport(self):
		if not self.live.registered:
			return
		lst = []
		for device in self.devices:
			if device.isSensor() is False:
				continue
			sensorFrame = []
			sensor = {
				'name': device.name(),
				'protocol': device.protocol(),
				'model': device.model(),
				'sensor_id': device.id(),
			}
			if device.params() and 'sensorId' in device.params():
				sensor['channelId'] = device.params()['sensorId']

			battery = device.battery()
			if battery is not None:
				sensor['battery'] = battery
			if hasattr(device, 'declaredDead') and device.declaredDead:
				# Sensor shouldn't be removed for a while, but don't update it on server side
				sensor['declaredDead'] = 1
			sensorFrame.append(sensor)
			valueList = []
			values = device.sensorValues()
			for valueType in values:
				for value in values[valueType]:
					valueList.append({
						'type': valueType,
						'lastUp': str(value['lastUpdated']),
						'value': str(value['value']),
						'scale': value['scale']
					})
					# Telldus Live! does not aknowledge sensorreportupdates yet,
					# so don't count this yet (wait for Cassandra only)
					# device.lastUpdatedLive[valueType] = int(time.time())
			sensorFrame.append(valueList)
			lst.append(sensorFrame)
		msg = LiveMessage("SensorsReport")
		msg.append(lst)
		self.live.send(msg)

	def sensorsUpdated(self):
		self.__sendSensorReport()
