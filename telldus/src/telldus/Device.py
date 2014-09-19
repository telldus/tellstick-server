# -*- coding: utf-8 -*-


class Device(object):
	TURNON  = 1
	TURNOFF = 2

	TEMPERATURE = 1
	HUMIDITY = 2

	def __init__(self):
		super(Device,self).__init__()
		self._id = 0
		self._name = None
		self._manager = None
		self._state = Device.TURNOFF
		self._stateValue = ''
		self._sensorValues = {}

	def id(self):
		return self._id

	def command(self, action, success=None, failure=None, callbackArgs=[]):
		pass

	def load(self, settings):
		if 'id' in settings:
			self._id = settings['id']
		if 'name' in settings:
			self._name = settings['name']
		if 'params' in settings:
			self.setParams(settings['params'])

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
		if valueType != Device.TEMPERATURE and valueType != Device.HUMIDITY:
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
