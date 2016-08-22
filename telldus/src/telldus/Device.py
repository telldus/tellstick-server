# -*- coding: utf-8 -*-

import logging

class DeviceAbortException(Exception):
	pass

class Device(object):
	"""
	A base class for a device. Any plugin adding devices must subclass this class.
	"""
	TURNON  = 1  #: Device flag for devices supporting the on method.
	TURNOFF = 2  #: Device flag for devices supporting the off method.
	BELL = 4     #: Device flag for devices supporting the bell method.
	DIM = 16     #: Device flag for devices supporting the dim method.
	LEARN = 32   #: Device flag for devices supporting the learn method.
	UP = 128     #: Device flag for devices supporting the up method.
	DOWN = 256   #: Device flag for devices supporting the down method.
	STOP = 512   #: Device flag for devices supporting the stop method.
	RGBW = 1024  #: Device flag for devices supporting the rgbw method.
	THERMOSTAT = 2048  #: Device flag for devices supporting thermostat methods.

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
	SCALE_POWER_WATT = 2
	SCALE_LUMINANCE_PERCENT = 0
	SCALE_LUMINANCE_LUX = 1

	FAILED_STATUS_RETRIES_FAILED = 1
	FAILED_STATUS_NO_REPLY = 2
	FAILED_STATUS_TIMEDOUT = 3
	FAILED_STATUS_NOT_CONFIRMED = 4

	def __init__(self):
		super(Device,self).__init__()
		self._id = 0
		self._battery = None
		self._loadCount = 0
		self._name = None
		self._manager = None
		self._state = Device.TURNOFF
		self._stateValue = ''
		self._sensorValues = {}
		self._confirmed = True

	def id(self):
		return self._id

	def battery(self):
		return self._battery

	def command(self, action, value=None, origin=None, success=None, failure=None, callbackArgs=[], ignore=None):
		"""This method executes a method with the device. This method must not be
		subclassed. Please subclass :func:`_command()` instead.

		  :param action: description
		  :return: return description

		Here below is the results of the :func:`Device.methods()` docstring.
		"""
		# Prevent loops from groups and similar
		if ignore is None:
			ignore = []
		if self.id() in ignore:
			return
		ignore.append(self.id())
		if type(action) == str or type(action) == unicode:
			method = Device.methodStrToInt(action)
		else:
			method = action
		if method == Device.DIM:
			if value is None:
				value = 0  # this is an error, but at least won't crash now
			else:
				value = int(value)
		elif method == Device.RGBW:
			if type(value) == str:
				value = int(value, 16)
			elif type(value) is not int:
				value = 0
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
		except Exception as e:
			logging.exception(e)
			triggerFail(0)

	def _command(self, action, value, success, failure, **kwargs):
		"""Reimplement this method to execute an action to this device."""
		failure(0)

	def confirmed(self):
		return self._confirmed

	def containingDevices(self):
		return []

	def flattenContainingDevices(self):
		devices = []
		ids = []
		toCheck = list(self.containingDevices())
		while len(toCheck):
			d = toCheck.pop()
			if type(d) is int:
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

	def loadCached(self, olddevice):
		self._id = olddevice._id
		self._name = olddevice._name
		self._loadCount = 0
		self.setParams(olddevice.params())
		(state, stateValue) = olddevice.state()
		self._state = state
		self._stateValue = stateValue
		self._battery = olddevice._battery

	def loadCount(self):
		return self._loadCount

	def load(self, settings):
		if 'id' in settings:
			self._id = settings['id']
		if 'name' in settings:
			self._name = settings['name']
		if 'params' in settings:
			self.setParams(settings['params'])
		#if 'state' in settings and 'stateValue' in settings:
		#	self.setState(settings['state'], settings['stateValue'])

	def localId(self):
		"""
		This method must be reimplemented in the subclass. Return a unique id for
		this device type.
		"""
		return 0

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

	def methods(self):
		"""
		Return the methods this supports. This is an or-ed in of device method flags.

		Example:
		return Device.TURNON | Device.TURNOFF
		"""
		return 0

	def model(self):
		return 'n/a'

	def name(self):
		return self._name if self._name is not None else 'Device %i' % self._id

	def params(self):
		return {}

	def paramUpdated(self, param):
		if self._manager:
			self._manager.save()

	def protocol(self):
		return self.typeString()

	def sensorValue(self, valueType, scale):
		if valueType not in self._sensorValues:
			return None
		for sensorType in self._sensorValues[valueType]:
			if sensorType['scale'] == scale:
				return sensorType['value']
		return None

	def sensorValues(self):
		return self._sensorValues

	def setId(self, id):
		self._id = id

	def setManager(self, manager):
		self._manager = manager

	def setName(self, name):
		self._name = name
		self.paramUpdated('name')

	def setParams(self, params):
		pass

	def setSensorValue(self, valueType, value, scale):
		if valueType not in self._sensorValues:
			self._sensorValues[valueType] = []
		found = False
		for sensorType in self._sensorValues[valueType]:
			if sensorType['scale'] == scale:
				sensorType['value'] = value
				found = True
				break
		if not found:
			self._sensorValues[valueType].append({'value': value, 'scale': scale})
		if self._manager:
			self._manager.sensorValueUpdated(self, valueType, value, scale)

	def setState(self, state, stateValue = None, ack=None, origin=None):
		if stateValue is None:
			stateValue = ''
		self._state = state
		self._stateValue = stateValue
		if self._manager:
			self._manager.stateUpdated(self, ackId=ack, origin=origin)

	def setStateFailed(self, state, stateValue = '', reason = 0, origin=None):
		if self._manager:
			self._manager.stateUpdatedFail(self, state, stateValue, reason, origin)

	def state(self):
		return (self._state, self._stateValue)

	def typeString(self):
		"""
		Must be reimplemented by subclass. Return the type (transport) of this
		device. All devices from a plugin must have the same type.
		"""
		return ''

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
		if method == 'rgbw':
			return Device.RGBW
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
			#Device.GENRIC_METER: 'genmeter'
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

class CachedDevice(Device):
	def __init__(self, settings):
		super(CachedDevice, self).__init__()
		self.paramsStorage = {}
		self.load(settings)
		self._confirmed = False
		self._localId = 0
		self.mimikType = ''
		self.storedmethods = 0
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
		if 'stateValue' in settings:
			self._stateValue = settings['stateValue']
		if 'battery' in settings:
			self._battery = settings['battery']

	def localId(self):
		return self._localId

	def methods(self):
		return self.storedmethods

	def params(self):
		return self.paramsStorage

	def setParams(self, params):
		self.paramsStorage = params

	def typeString(self):
		return self.mimikType
