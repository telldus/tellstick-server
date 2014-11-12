# -*- coding: utf-8 -*-


class Device(object):
	TURNON  = 1
	TURNOFF = 2
	DIM = 16

	TEMPERATURE = 1
	HUMIDITY = 2
	WATT = 256
	LUMINANCE = 512

	def __init__(self):
		super(Device,self).__init__()
		self._id = 0
		self._name = None
		self._manager = None
		self._state = Device.TURNOFF
		self._stateValue = ''
		self._sensorValues = {}
		self._confirmed = True

	def id(self):
		return self._id

	def command(self, action, value=None, success=None, failure=None, callbackArgs=[]):
		pass

	def confirmed(self):
		return self._confirmed

	def loadCached(self, olddevice):
		self._id = olddevice._id
		self._name = olddevice._name
		self.setParams(olddevice.params())
		(state, stateValue) = olddevice.state()
		self.setState(state, stateValue)

	def load(self, settings):
		if 'id' in settings:
			self._id = settings['id']
		if 'name' in settings:
			self._name = settings['name']
		if 'params' in settings:
			self.setParams(settings['params'])
		if 'state' in settings and 'stateValue' in settings:
			self.setState(settings['state'], settings['stateValue'])

	def localId(self):
		return 0

	def isDevice(self):
		return True

	def isSensor(self):
		return False

	def methods(self):
		return 0

	def name(self):
		return self._name if self._name is not None else 'Device %i' % self._id

	def params(self):
		return {}

	def paramUpdated(self, param):
		if self._manager:
			self._manager.save()

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

	def setSensorValue(self, valueType, value):
		if valueType not in [Device.TEMPERATURE, Device.HUMIDITY, Device.WATT, Device.LUMINANCE]:
			# TODO(micke): Ignoring for now
			return
		self._sensorValues[valueType] = value
		if self._manager:
			self._manager.sensorValueUpdated(self)

	def setState(self, state, stateValue = ''):
		self._state = state
		self._stateValue = stateValue
		if self._manager:
			self._manager.stateUpdated(self)

	def state(self):
		return (self._state, self._stateValue)

	def typeString(self):
		return ''

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
		if 'type' in settings:
			self.mimikType = settings['type']
		if 'methods' in settings:
			self.storedmethods = settings['methods']

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
