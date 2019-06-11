# -*- coding: utf-8 -*-

import logging
import time

from base import Application

class DeviceAbortException(Exception):
	pass

# pylint: disable=R0904,R0902,C0103
class Device(object):
	"""
	A base class for a device. Any plugin adding devices must subclass this class.
	"""
	TURNON = 1  #: Device flag for devices supporting the on method.
	TURNOFF = 2  #: Device flag for devices supporting the off method.
	BELL = 4     #: Device flag for devices supporting the bell method.
	TOGGLE = 8   #: Device flag for devices supporting the toggle method.
	DIM = 16     #: Device flag for devices supporting the dim method.
	LEARN = 32   #: Device flag for devices supporting the learn method.
	EXECUTE = 64 #: Device flag for devices supporting the execute method.
	UP = 128     #: Device flag for devices supporting the up method.
	DOWN = 256   #: Device flag for devices supporting the down method.
	STOP = 512   #: Device flag for devices supporting the stop method.
	RGB = 1024   #: Device flag for devices supporting the rgb method.
	RGBW = 1024  #: Device flag for devices supporting the rgb method, this is depricated, use RGB.
	THERMOSTAT = 2048  #: Device flag for devices supporting thermostat methods.

	TYPE_UNKNOWN = '00000000-0001-1000-2005-ACCA54000000'
	TYPE_ALARM_SENSOR = '00000001-0001-1000-2005-ACCA54000000'
	TYPE_CONTAINER = '00000002-0001-1000-2005-ACCA54000000'
	TYPE_CONTROLLER = '00000003-0001-1000-2005-ACCA54000000'
	TYPE_DOOR_WINDOW = '00000004-0001-1000-2005-ACCA54000000'
	TYPE_LIGHT = '00000005-0001-1000-2005-ACCA54000000'
	TYPE_LOCK = '00000006-0001-1000-2005-ACCA54000000'
	TYPE_MEDIA = '00000007-0001-1000-2005-ACCA54000000'
	TYPE_METER = '00000008-0001-1000-2005-ACCA54000000'
	TYPE_MOTION = '00000009-0001-1000-2005-ACCA54000000'
	TYPE_ON_OFF_SENSOR = '0000000A-0001-1000-2005-ACCA54000000'
	TYPE_PERSON = '0000000B-0001-1000-2005-ACCA54000000'
	TYPE_REMOTE_CONTROL = '0000000C-0001-1000-2005-ACCA54000000'
	TYPE_SENSOR = '0000000D-0001-1000-2005-ACCA54000000'
	TYPE_SMOKE_SENSOR = '0000000E-0001-1000-2005-ACCA54000000'
	TYPE_SPEAKER = '0000000F-0001-1000-2005-ACCA54000000'
	TYPE_SWITCH_OUTLET = '00000010-0001-1000-2005-ACCA54000000'
	TYPE_THERMOSTAT = '00000011-0001-1000-2005-ACCA54000000'
	TYPE_VIRTUAL = '00000012-0001-1000-2005-ACCA54000000'
	TYPE_WINDOW_COVERING = '00000013-0001-1000-2005-ACCA54000000'
	TYPE_PROJECTOR_SCREEN = '00000014-0001-1000-2005-ACCA54000000'

	UNKNOWN = 0                 #: Sensor type flag for an unknown type
	TEMPERATURE = 1             #: Sensor type flag for temperature
	HUMIDITY = 2                #: Sensor type flag for humidity
	RAINRATE = 4                #: Sensor type flag for rain rate
	RAINTOTAL = 8               #: Sensor type flag for rain total
	WINDDIRECTION = 16          #: Sensor type flag for wind direction
	WINDAVERAGE	= 32            #: Sensor type flag for wind average
	WINDGUST = 64               #: Sensor type flag for wind gust
	UV = 128                    #: Sensor type flag for uv
	WATT = 256                  #: Sensor type flag for watt
	LUMINANCE = 512             #: Sensor type flag for luminance
	DEW_POINT = 1024            #: Sensor type flag for dew point
	BAROMETRIC_PRESSURE = 2048  #: Sensor type flag for barometric pressure
	GENERIC_METER = 4096		#: Sensor type flag for generic meter
	CO2 = 8192					#: Sensor type flag for CO²
	VOLUME = 16384				#: Sensor type flag for volume
	LOUDNESS = 32768			#: Sensor type flag for loudness
	PM25 = 65536				#: Sensor type flag for particulate matter 2.5
	CO = 131072					#: Sensor type flag for CO
	WEIGHT = 262144				#: Sensor type flag for weight
	MOISTURE = 524288			#: Sensor type flag for moisture

	SCALE_UNKNOWN = 0
	SCALE_TEMPERATURE_CELCIUS = 0
	SCALE_TEMPERATURE_FAHRENHEIT = 1
	SCALE_HUMIDITY_PERCENT = 0
	SCALE_RAINRATE_MMH = 0
	SCALE_RAINTOTAL_MM = 0
	SCALE_WIND_VELOCITY_MS = 0
	SCALE_WIND_DIRECTION = 0
	SCALE_UV_INDEX = 0
	SCALE_POWER_KWH = 0
	SCALE_POWER_KVAH = 1
	SCALE_POWER_WATT = 2
	SCALE_POWER_PULSE = 3
	SCALE_POWER_VOLT = 4
	SCALE_POWER_AMPERE = 5
	SCALE_POWER_POWERFACTOR = 6
	SCALE_LUMINANCE_PERCENT = 0
	SCALE_LUMINANCE_LUX = 1
	SCALE_BAROMETRIC_PRESSURE_KPA = 0
	SCALE_PULSE = 0
	SCALE_PPM = 1
	SCALE_LITRE = 0
	SCALE_M3 = 1
	SCALE_DB = 0
	SCALE_DBA = 1
	SCALE_MICROGPERM3 = 1
	SCALE_KG = 0

	FAILED_STATUS_RETRIES_FAILED = 1
	FAILED_STATUS_NO_REPLY = 2
	FAILED_STATUS_TIMEDOUT = 3
	FAILED_STATUS_NOT_CONFIRMED = 4
	FAILED_STATUS_UNKNOWN = 5

	BATTERY_LOW = 255  # Battery status, if not percent value
	BATTERY_UNKNOWN = 254  # Battery status, if not percent value
	BATTERY_OK = 253  # Battery status, if not percent value

	def __init__(self):
		super(Device, self).__init__()
		self._id = 0
		self._ignored = None
		self._loadCount = 0
		self._name = None
		self._metadata = {}
		self._manager = None
		self._room = None
		self._state = Device.TURNOFF
		self._stateValues = {}
		self._sensorValues = {}
		self._confirmed = True
		self.valueChangedTime = {}
		self.lastUpdated = None  # internal use only, last time state was changed
		self.lastUpdatedLive = {}

	def id(self):
		return self._id

	def allParameters(self):
		"""
		Similar as parameters() but this returnes more values such as the device type and the room
		"""
		params = self.parameters()
		if isinstance(params, dict):
			# Copy so we don't alter the original
			params = params.copy()
		else:
			# parameters() must return a dict
			params = {}

		devicetype = self.metadata('devicetype', None)
		if devicetype is not None:
			# Devicetype in metadata overrides the devicetype
			params['devicetype'] = devicetype
		else:
			try:
				params['devicetype'] = self.deviceType()
			except Exception as error:
				params['devicetype'] = Device.TYPE_UNKNOWN
				Application.printException(error)
		if self._room is None:
			# Make sure it's removed
			params.pop('room', None)
		else:
			params['room'] = self._room
		return params

	def battery(self):  # pylint: disable=R0201
		"""
		Returns the current battery value
		"""
		return None

	# pylint: disable=R0913
	def command(self, action, value=None, origin=None, success=None,
	            failure=None, callbackArgs=None, ignore=None):
		"""
		This method executes a method with the device. This method must not be
		subclassed. Please subclass :func:`_command()` instead.

		:param action: description
		:return: return description

		Here below is the results of the :func:`Device.methods()` docstring.
		"""
		if callbackArgs is None:
			callbackArgs = []
		# Prevent loops from groups and similar
		if ignore is None:
			ignore = []
		if self.id() in ignore:
			return
		ignore.append(self.id())
		if isinstance(action, str) or isinstance(action, unicode):
			method = Device.methodStrToInt(action)
		else:
			method = action
		if method == Device.DIM:
			if value is None:
				value = 0  # this is an error, but at least won't crash now
			else:
				value = int(value)
		elif method == Device.RGB:
			if isinstance(value, str):
				value = int(value, 16)
			elif not isinstance(value, int):
				value = 0
			if action == 'rgbw':
				# For backwards compatibility, remove white component
				value = value >> 8
		elif method == Device.THERMOSTAT:
			pass
		else:
			value = None
		def triggerFail(reason):
			if failure:
				try:
					failure(reason, *callbackArgs)
				except DeviceAbortException:
					return
		def s(state=None, stateValue=None):
			if state is None:
				state = method
			if stateValue is None:
				stateValue = value
			if success:
				try:
					success(state=state, stateValue=stateValue, *callbackArgs)
				except DeviceAbortException:
					return
			self.setState(state, stateValue, origin=origin)

		if method == 0:
			triggerFail(0)
			return
		try:
			self._command(method, value, success=s, failure=triggerFail, ignore=ignore)
		except Exception as error:
			Application.printException(error)
			triggerFail(0)

	# pylint: disable=R0201,W0613
	def _command(self, action, value, success, failure, **__kwargs):
		"""Reimplement this method to execute an action to this device."""
		failure(0)

	def confirmed(self):
		return self._confirmed

	def containingDevices(self):
		return []

	def deviceType(self):
		return Device.TYPE_UNKNOWN

	def flattenContainingDevices(self):
		devices = []
		ids = []
		toCheck = list(self.containingDevices())
		while len(toCheck):
			d = toCheck.pop()
			if isinstance(d, int):
				d = self._manager.device(d)
			if d is None:
				continue
			if d is self:
				# Ignore ourself
				continue
			if d.id() in ids:
				continue
			devices.append(d)
			ids.append(d.id())
			toCheck.extend(d.containingDevices())
		return devices

	# pylint: disable=W0212
	def loadCached(self, olddevice):
		self._id = olddevice._id
		self._name = olddevice._name
		self._loadCount = 0
		self.setParams(olddevice.params())
		(state, __stateValue) = olddevice.state()
		self._metadata = olddevice._metadata
		self._room = olddevice._room
		self._state = state
		self._stateValues = olddevice.stateValues()
		self._ignored = olddevice._ignored
		self._sensorValues = olddevice._sensorValues

	def loadCount(self):
		return self._loadCount

	def load(self, settings):
		if 'id' in settings:
			self._id = settings['id']
		if 'metadata' in settings:
			self._metadata = settings['metadata']
		if 'name' in settings:
			self._name = settings['name']
		if 'params' in settings:
			self.setParams(settings['params'])
		if 'room' in settings:
			self._room = settings['room']
		#if 'state' in settings and 'stateValue' in settings:
		#	self.setState(settings['state'], settings['stateValue'])

	def localId(self):
		"""
		This method must be reimplemented in the subclass. Return a unique id for
		this device type.
		"""
		return 0

	def ignored(self):
		return self._ignored

	def isDevice(self):
		"""
		Return True if this is a device.
		"""
		return True

	def isSensor(self):
		"""
		Return True if this is a sensor.
		"""
		return False

	def manager(self):
		return self._manager

	def metadata(self, key=None, default=None):
		"""
		Returns a metadata value set by the user. If key is none then all values are returned as
		a dictionary.
		"""
		if key is None:
			return self._metadata.copy()
		return self._metadata.get(key, default)

	def methods(self):
		"""
		This function returns the methods this device supports.

		:returns: An or-ed integer of device method flags.

		Example:

		.. code-block:: python

		  return Device.TURNON | Device.TURNOFF
		"""
		return 0

	def model(self):
		return 'n/a'

	def name(self):
		return self._name if self._name is not None else 'Device %i' % self._id

	def parameters(self):
		"""
		:returns: a static dictionary of paramters describing the device.
		  These should not contain the current state of the device, only descriptive parameters.
		"""
		return {}

	def params(self):
		return {}

	def paramUpdated(self, param):
		if self._manager:
			self._manager.deviceParamUpdated(self, param)

	def protocol(self):
		return self.typeString()

	def room(self):
		"""
		:returns: The current room this device belongs to
		"""
		return self._room

	def sensorElement(self, valueType, scale):
		"""
		:returns: a sensor value and lastUpdated-time, as a dict, of a the specified
		  valueType and scale. Returns ``None`` is no such value exists
		"""
		if valueType not in self._sensorValues:
			return None
		for sensorType in self._sensorValues[valueType]:
			if sensorType['scale'] == scale:
				lastUpdated = None
				if 'lastUpdated' in sensorType:
					lastUpdated = sensorType['lastUpdated']
				return {'value': float(sensorType['value']), 'lastUpdated': lastUpdated}
		return None

	def sensorValue(self, valueType, scale):
		"""
		:returns: a sensor value of a the specified valueType and scale. Returns ``None``
		  is no such value exists
		"""
		if valueType not in self._sensorValues:
			return None
		for sensorType in self._sensorValues[valueType]:
			if sensorType['scale'] == scale:
				return float(sensorType['value'])
		return None

	def sensorValues(self):
		"""
		:returns: a list of all sensor values this device has received.
		"""
		return self._sensorValues

	def setId(self, newId):
		self._id = newId

	def setIgnored(self, ignored):
		self._ignored = ignored
		if self._manager:
			self._manager.save()

	def setManager(self, manager):
		self._manager = manager

	def setMetadata(self, name, value):
		if self._metadata.get(name, None) == value:
			# Identical, do nothing
			return
		if value is None or value == '':
			# Remove it
			self._metadata.pop(name, None)
		else:
			self._metadata[name] = value
		if self._manager:
			self._manager.deviceMetadataUpdated(self, name)

	def setName(self, name):
		self._name = name
		self.paramUpdated('name')

	def setParameter(self, name, value):
		"""
		Set a device specific parameter. What kind of paramters to set is dependent on the device
		type
		"""
		pass

	def setParams(self, params):
		pass

	def setRoom(self, room):
		"""
		Adds the device to a room.
		Set to None or empty string to remove from room
		"""
		room = None if room == '' else room
		if self._room == room:
			# Don't fire update if not changed
			return
		self._room = room
		self.paramUpdated('room')

	def setSensorValue(self, valueType, value, scale):
		self.setSensorValues([{'type': valueType, 'value':value, 'scale': scale}])

	def setSensorValues(self, values):
		withinOneSecond = None
		for valueElement in values:
			valueType = valueElement['type']
			value = valueElement['value']
			scale = valueElement['scale']
			if valueType not in self._sensorValues:
				self._sensorValues[valueType] = []
			found = False
			for sensorType in self._sensorValues[valueType]:
				if sensorType['scale'] == scale:
					if sensorType['value'] != str(value) or valueType not in self.valueChangedTime:
						# value has changed
						self.valueChangedTime[valueType] = int(time.time())
						withinOneSecond = False
					else:
						if sensorType['lastUpdated'] > int(time.time() - 1):
							# Same value and less than a second ago, most probably
							# just the same value being resent, ignore
							if withinOneSecond is None:
								# if it has been explicitly set to False, don't change it
								withinOneSecond = True
							found = True
							break
						else:
							withinOneSecond = False
					sensorType['value'] = str(value)
					sensorType['lastUpdated'] = int(time.time())
					found = True
					break
			if not found and not withinOneSecond:
				self._sensorValues[valueType].append({
					'value': str(value),
					'scale': scale,
					'lastUpdated': int(time.time())
				})
				self.valueChangedTime[valueType] = int(time.time())
		if self._manager and not withinOneSecond:
			self._manager.sensorValuesUpdated(self, values)
			self._manager.save()

	def setState(self, state, stateValue=None, ack=None, origin=None, onlyUpdateIfChanged=False):
		"""
		Update the state of the device. Use this method if the state should be updated from an
		external source and not by an command. Examples if the state was updated on the device
		itself.

		:param state: The new state
		:param stateValue: State value for the state if needed. Not all states has values.
		:param ack: Internal, do not use
		:param origin: The origin how the state was updated. If not set this will be "Incoming signal"
		:param onlyUpdateIfChanged: Skip the update if the state is changed or not. If this is `False`
		       the new state will always trigger and update. This parameter was added in version 1.2
		"""
		if stateValue is None:
			stateValue = ''
		if self._state == state and self._stateValues.get(state, None) == stateValue:
			if self.lastUpdated and self.lastUpdated > int(time.time() - 1):
				# Same state/statevalue and less than one second ago, most probably
				# just the same value being resent, ignore
				return
			if onlyUpdateIfChanged:
				# No need to update
				return
		self.lastUpdated = time.time()
		if state in (Device.DIM, Device.RGB, Device.THERMOSTAT) \
		   and stateValue is not None and stateValue is not '':
			self._stateValues[str(state)] = stateValue

		if state not in (Device.EXECUTE, Device.LEARN, Device.RGB):
			# don't change the state itself for some types
			self._state = state

		if self._manager:
			self._manager.stateUpdated(self, ackId=ack, origin=origin)

	def setStateFailed(self, state, stateValue=None, reason=0, origin=None):
		if self._manager:
			self._manager.stateUpdatedFail(self, state, stateValue, reason, origin)

	def state(self):
		"""
		:returns: a tuple of the device state and state value

		  Example:

		  .. code-block:: python

		     state, stateValue = device.state()
		"""
		return (self._state, self.stateValue())

	def stateValue(self, state=None):
		"""
		.. versionadded:: 1.2

		:returns: The statevalue for the specified state.
		:param state: The state to request the value for. If no state is specified the current state
		              is used
		:type state: int or None
		"""
		state = state or self._state
		return self._stateValues.get(str(state), '')

	def stateValues(self):
		"""
		.. versionadded:: 1.2

		:returns: a dict of all state values for the device
		"""
		return self._stateValues

	def typeString(self):
		"""
		Must be reimplemented by subclass. Return the type (transport) of this
		device. All devices from a plugin must have the same type.
		"""
		return ''

	# pylint: disable=R0911
	@staticmethod
	def methodStrToInt(method):
		"""Convenience method to convert method string to constants.

		Example:
		"turnon" => Device.TURNON
		"""
		if method == 'turnon':
			return Device.TURNON
		if method == 'turnoff':
			return Device.TURNOFF
		if method == 'dim':
			return Device.DIM
		if method == 'bell':
			return Device.BELL
		if method == 'learn':
			return Device.LEARN
		if method == 'up':
			return Device.UP
		if method == 'down':
			return Device.DOWN
		if method == 'stop':
			return Device.STOP
		if method == 'rgb' or method == 'rgbw':
			return Device.RGB
		if method == 'thermostat':
			return Device.THERMOSTAT
		logging.warning('Did not understand device method %s', method)
		return 0

	@staticmethod
	def maskUnsupportedMethods(methods, supportedMethods):
		# Up -> Off
		if (methods & Device.UP) and not (supportedMethods & Device.UP):
			methods = methods | Device.TURNOFF

		# Down -> On
		if (methods & Device.DOWN) and not (supportedMethods & Device.DOWN):
			methods = methods | Device.TURNON

		# Cut of the rest of the unsupported methods we don't have a fallback for
		return methods & supportedMethods

	@staticmethod
	def sensorTypeIntToStr(sensorType):
		types = {
			Device.TEMPERATURE: 'temp',
			Device.HUMIDITY: 'humidity',
			Device.RAINRATE: 'rrate',
			Device.RAINTOTAL: 'rtot',
			Device.WINDDIRECTION: 'wdir',
			Device.WINDAVERAGE: 'wavg',
			Device.WINDGUST: 'wgust',
			Device.UV: 'uv',
			Device.WATT: 'watt',
			Device.LUMINANCE: 'lum',
			Device.DEW_POINT: 'dewp',
			Device.BAROMETRIC_PRESSURE: 'barpress',
			Device.GENRIC_METER: 'genmeter',
			Device.WEIGHT: 'weight',
			Device.CO2: 'co2',
			Device.VOLUME: 'volume',
			Device.LOUDNESS: 'loudness',
			Device.PM25: 'particulatematter25',
			Device.CO: 'co',
			Device.MOISTURE: 'moisture'
		}
		return types.get(sensorType, 'unknown')

class Sensor(Device):
	"""A convenience class for sensors."""
	def isDevice(self):
		return False

	def isSensor(self):
		return True

	def name(self):
		return self._name if self._name is not None else 'Sensor %i' % self._id

class CachedDevice(Device):  # pylint: disable=R0902
	def __init__(self, settings):
		super(CachedDevice, self).__init__()
		self.paramsStorage = {}
		self.load(settings)
		self._confirmed = False
		self._localId = 0
		self.mimikType = ''
		self.storedmethods = 0
		self.batteryLevel = Device.BATTERY_UNKNOWN
		self._isSensor = False
		if 'localId' in settings:
			self._localId = settings['localId']
		if 'loadCount' in settings:
			self._loadCount = settings['loadCount']+1
		if 'type' in settings:
			self.mimikType = settings['type']
		if 'methods' in settings:
			self.storedmethods = settings['methods']
		if 'state' in settings:
			self._state = settings['state']
		if 'stateValues' in settings:
			self._stateValues = settings['stateValues']
		if 'stateValue' in settings and settings['stateValue'] is not None:
			self._stateValues[str(self._state)] = settings['stateValue']
		if 'battery' in settings:
			self.batteryLevel = settings['battery']
		if 'ignored' in settings:
			self._ignored = settings['ignored']
		if 'sensorValues' in settings:
			self.fillSensorValues(settings['sensorValues'])
		if 'isSensor' in settings:
			self._isSensor = settings['isSensor']
		if 'declaredDead' in settings:
			self.declaredDead = settings['declaredDead']

	def isSensor(self):
		return self._isSensor

	def localId(self):
		return self._localId

	def methods(self):
		return self.storedmethods

	def params(self):
		return self.paramsStorage

	def setParams(self, params):
		self.paramsStorage = params

	def fillSensorValues(self, sensorValues):
		# this method just fills cached values, no signals or reports are sent
		for valueTypeFetch in sensorValues:
			valueType = int(valueTypeFetch)
			if valueType not in self._sensorValues:
				self._sensorValues[valueType] = []
			sensorType = sensorValues[valueTypeFetch]
			for sensorValue in sensorType:
				value = sensorValue['value']
				scale = sensorValue['scale']
				if 'lastUpdated' in sensorValue:
					lastUpdated = sensorValue['lastUpdated']
				else:
					# not in cache, perhaps first time lastUpdated is used
					# (maybe this should be logged?)
					lastUpdated = int(time.time())
				self._sensorValues[valueType].append({
					'value': value,
					'scale': scale,
					'lastUpdated': lastUpdated
				})

	def typeString(self):
		return self.mimikType
