# -*- coding: utf-8 -*-

class PluginContext(object):
	def __init__(self):
		self.components = {}

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
		c = [cls(component.context) for cls in classes]
		return Observers(self.interface, c)

class IInterface(object):
	"""Base class for interfaces"""

class PluginMeta(type):
	_registry = {}

	def __new__(mcs, name, bases, d):
		newClass = type.__new__(mcs, name, bases, d)
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
			self.context = context
			self.__init__()
			context.components[cls] = self
		return self

class Plugin(object):
	__metaclass__ = PluginMeta

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
