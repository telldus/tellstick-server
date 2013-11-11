# -*- coding: utf-8 -*-


class Device(object):
	def __init__(self):
		super(Device,self).__init__()
		self._id = 0
		self._name = None

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

	def name(self):
		return self._name if self._name is not None else 'Device %i' % self._id

	def params(self):
		return {}

	def setId(self, id):
		self._id = id

	def setParams(self, params):
		pass

	def typeString(self):
		return ''
