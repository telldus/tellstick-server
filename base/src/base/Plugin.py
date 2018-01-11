# -*- coding: utf-8 -*-

import logging
from six import add_metaclass

class PluginContext(object):
	def __init__(self):
		self.components = {}

	def request(self, name):
		if name not in PluginMeta._plugins:
			return None
		return PluginMeta._plugins[name](self)

	def pluginsList(self):
		return [x for x in PluginMeta._plugins if PluginMeta._plugins[x].public == True]

class Observers(object):
	def __init__(self, interface, observers):
		self.interface = interface
		self.observers = observers

	def __getattr__(self, name):
		if not hasattr(self.interface, name):
			raise AttributeError("'%s' object has no attribute '%s'" % (repr(self.interface), name))
		def fn(*args, **kwargs):
			for o in self.observers:
				try:
					m = getattr(o, name)
				except:
					continue
				m(*args, **kwargs)
		return fn

	def __len__(self):
		return len(self.observers)

	def __iter__(self):
		return iter(self.observers)

class ObserverCollection(property):
	def __init__(self, interface):
		property.__init__(self, self.extensions)
		self.interface = interface

	def extensions(self, component):
		classes = PluginMeta._registry.get(self.interface, ())
		if not hasattr(component, 'context'):
			raise AttributeError("'%s' object has no attribute '%s'" % (repr(component), 'context'))
		c = []
		for cls in classes:
			try:
				c.append(cls(component.context))
			except Exception as e:
				logging.exception(e)
		return Observers(self.interface, c)

class IInterface(object):
	"""Base class for interfaces"""

class PluginMeta(type):
	_registry = {}
	_plugins = {}

	def __new__(mcs, name, bases, d):
		newClass = type.__new__(mcs, name, bases, d)
		PluginMeta._plugins['%s.%s' % (newClass.__module__, newClass.__name__)] = newClass
		for cls in newClass.__mro__:
			for interface in cls.__dict__.get('_implements', []):
				classes = PluginMeta._registry.setdefault(interface, [])
				if newClass not in classes:
					classes.append(newClass)
		return newClass

	def __call__(cls, *args, **kwargs):
		assert len(args) >= 1 and isinstance(args[0], PluginContext), \
		       "First argument must be a PluginContext instance"
		context = args[0]
		self = context.components.get(cls)
		if self is None:
			self = cls.__new__(cls)
			# If the class implements any observer pattern before our __init__
			# function has been called the observed function may be called before
			# the class has been initialized completely. A proper fix should be to
			# not call observed functions before the class has been fully loaded.
			context.components[cls] = self
			self.context = context
			self.__init__()
		return self

@add_metaclass(PluginMeta)
class Plugin(object):

	public = False

	def tearDown(self):
		pass

	def __getattr__(self, name):
		for i in self._implements:
			m = i.__dict__.get(name)
			if m:
				return m
		raise AttributeError("'%s' object has no attribute '%s'" % (repr(self), name))

	@staticmethod
	def implements(*interfaces):
		import sys
		frame = sys._getframe(1)
		frame.f_locals.setdefault('_implements', []).extend(interfaces)

implements = Plugin.implements
