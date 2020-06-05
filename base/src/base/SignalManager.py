# -*- coding: utf-8 -*-

import sys
import types

from .Application import Application
from .Plugin import IInterface, ObserverCollection, Plugin

class ISignalObserver(IInterface):
	"""Implement this IInterface to recieve signals using the decorator :py:func:`@slot <base.slot>`"""

class Signal(object):
	def __init__(self, fn):
		self.func = fn

	def doc(self):
		doc = self.func.__doc__ if self.func.__doc__ is not None else ''
		return doc.strip()

	def args(self):
		return list(self.func.func_code.co_varnames)[1:self.func.func_code.co_argcount]

class SignalManager(Plugin):
	observers = ObserverCollection(ISignalObserver)
	signals = {}

	def observersForSignal(self, signalName):
		"""
		Return a list of methods and their options as a tuple for the given signal
		"""
		observers = []
		for observer in self.observers:
			listeners = getattr(observer, '_applicationSlots', {}).get(signalName, [])
			for listener, opts in listeners:
				# Bind the methods
				func = listener.__get__(observer, observer.__class__)
				observers.append((func, opts))
		return observers

	def sendSignal(self, msg, *args, **kwargs):
		for observer in self.observers:
			for func, opts in getattr(observer, '_applicationSlots', {}).get(msg, []):
				Application().queue(func, observer, *args, **kwargs)
			for func, opts in getattr(observer, '_applicationSlots', {}).get('', []):
				Application().queue(func, observer, msg, *args, **kwargs)

	@staticmethod
	def slot(message='', **opts):
		def call(func):
			frame = sys._getframe(1)  # pylint: disable=W0212
			frame.f_locals.setdefault('_applicationSlots',
			                          {}).setdefault(message,
			                                         []).append((
			                                             func,
			                                             opts,
			                                         ))
			return func
		return call

	@staticmethod
	def signal(name=None):
		def call(func, *__args, **__kwargs):
			SignalManager.signals[name if isinstance(name, str) else func.__name__] = Signal(func)
			def wrapper(obj, *args, **kwargs):
				signalName = name if isinstance(name, str) else func.__name__
				ctx = obj.context if hasattr(obj, 'context') else Application().pluginContext
				retval = func(obj, *args, **kwargs)
				SignalManager(ctx).sendSignal(signalName, *args, **kwargs)
				return retval
			return wrapper
		if isinstance(name, str) or name is None:
			# decorator is used like this @signal() or @signal('name')
			return call
		if isinstance(name, types.FunctionType):
			# decorator is used like this @signal
			return call(name)
		return None

signal = SignalManager.signal  # pylint: disable=C0103
slot = SignalManager.slot  # pylint: disable=C0103
