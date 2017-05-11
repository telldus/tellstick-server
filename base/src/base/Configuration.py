# -*- coding: utf-8 -*-

from .Plugin import Plugin, PluginMeta
from .Settings import Settings
import logging

class configuration(object):
	""".. py:decorator:: configuration

	This decorator specifies the configurations for a plugin."""
	def __init__(self, **kwargs):
		self.config = kwargs

	def __call__(self, cls):
		def config(self, key):
			return ConfigurationManager(self.context).value(self, key)
		def setConfig(self, key, value):
			ConfigurationManager(self.context).setValue(self, key, value)
		cls.configuration = self.config
		cls.config = config
		cls.setConfig = setConfig
		return cls

class ConfigurationValue(object):
	def __init__(self, valueType, defaultValue, writable=True, readable=True, hidden=False, **kwargs):
		self.valueType = valueType
		self.defaultValue = defaultValue
		self.readable = readable
		self.writable = writable
		self.hidden = hidden
		self.title = kwargs.setdefault('title', '')
		self.description = kwargs.setdefault('description', '')

	def serialize(self):
		return {
			'description': self.description,
			'hidden': self.hidden,
			'readable': self.readable,
			'title': self.title,
			'type': self.valueType,
			'writable': self.writable,
		}

class ConfigurationDict(ConfigurationValue):
	def __init__(self, defaultValue={}, **kwargs):
		super(ConfigurationDict,self).__init__('dict', defaultValue, **kwargs)

class ConfigurationList(ConfigurationValue):
	def __init__(self, defaultValue=[], **kwargs):
		super(ConfigurationList,self).__init__('list', defaultValue, **kwargs)

class ConfigurationNumber(ConfigurationValue):
	def __init__(self, defaultValue=0, **kwargs):
		super(ConfigurationNumber,self).__init__('number', defaultValue, **kwargs)

class ConfigurationString(ConfigurationValue):
	def __init__(self, defaultValue='', minLength=0, maxLength=0, **kwargs):
		self.minLength = minLength
		self.maxLength = maxLength
		super(ConfigurationString,self).__init__('string', defaultValue, **kwargs)

	def serialize(self):
		retval = super(ConfigurationString,self).serialize()
		retval['minLength'] = self.minLength
		retval['maxLength'] = self.maxLength
		return retval

class ConfigurationManager(Plugin):
	def configForClass(self, cls):
		if hasattr(cls, 'configuration') is False:
			return None
		cfgObj = {}
		for key in cls.configuration:
			config = cls.configuration[key].serialize()
			if config['hidden'] == True:
				continue
			if config['title'] == '':
				config['title'] = key
			if config['readable'] == True:
				config['value'] = self.__getValue(cls, key)
			cfgObj[key] = config
		return cfgObj

	def setValue(self, callee, key, value):
		s = Settings(ConfigurationManager.nameForObject(callee))
		s[key] = value
		if hasattr(callee, 'configWasUpdated'):
			callee(self.context).configWasUpdated(key, value)

	def value(self, callee, key):
		return self.__getValue(callee.__class__, key)

	def __getValue(self, cls, key):
		name = ConfigurationManager.nameForClass(cls)
		# Find out the default value, used to parse the value correctly
		if key not in cls.configuration:
			logging.warning("%s not in %s", key, cls.configuration)
			return None
		s = Settings(name)
		value = s.get(key, cls.configuration[key].defaultValue)
		if value is not None:
			return value

	def __requestConfigurationObject(self, obj, name):
		cfg = obj.getConfiguration()
		if name not in cfg:
			return None
		return cfg[name]

	@staticmethod
	def nameForObject(obj):
		if isinstance(obj, PluginMeta):
			return ConfigurationManager.nameForClass(obj)
		if isinstance(obj, Plugin):
			return ConfigurationManager.nameForInstance(obj)
		raise Exception('Object is not a subclass of Plugin')

	@staticmethod
	def nameForClass(cls):
		return '%s.%s' % (cls.__module__, cls.__name__)

	@staticmethod
	def nameForInstance(instance):
		return ConfigurationManager.nameForClass(instance.__class__)
