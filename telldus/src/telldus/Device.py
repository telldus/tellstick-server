# -*- coding: utf-8 -*-


class Device(object):
	TURNON  = 1
	TURNOFF = 2

	def __init__(self):
		super(Device,self).__init__()
		self._id = 0
		self._name = None
		self._manager = None
		self._state = Device.TURNOFF
		self._stateValue = ''

	def id(self):
		return self._id

	def command(self, action):
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

	def methods(self):
		return 0

	def name(self):
		return self._name if self._name is not None else 'Device %i' % self._id

	def params(self):
		return {}

	def paramUpdated(self, param):
		if self._manager:
			self._manager.save()

	def setId(self, id):
		self._id = id

	def setManager(self, manager):
		self._manager = manager

	def setName(self, name):
		self._name = name
		self.paramUpdated('name')

	def setParams(self, params):
		pass

	def setState(self, state, stateValue = ''):
		self._state = state
		self._stateValue = stateValue
		if self._manager:
			self._manager.stateUpdated(self)

	def state(self):
		return (self._state, self._stateValue)

	def typeString(self):
		return ''
