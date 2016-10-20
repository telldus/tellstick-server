# -*- coding: utf-8 -*-

from Application import Application
from Plugin import IInterface, ObserverCollection, Plugin
import sys, types

class ISignalObserver(IInterface):
	"""Implement this IInterface to recieve signals using the decorator :func:`@slot`"""

class Signal(object):
	def __init__(self, fn):
		self.fn = fn

class SignalManager(Plugin):
	observers = ObserverCollection(ISignalObserver)
	signals = {}

	def sendSignal(self, msg, *args, **kwargs):
		for o in self.observers:
			for f in getattr(o, '_applicationSlots', {}).get(msg, []):
				Application().queue(f, o, *args, **kwargs)
			for f in getattr(o, '_applicationSlots', {}).get('', []):
				Application().queue(f, o, msg, *args, **kwargs)

	@staticmethod
	def slot(message = ''):
		""".. py:decorator:: slot

		This is a decorator for receiveing signals. The class must implement
		:class:`ISignalObserver`

		Args:
		  :message: This is the signal name to receive
		"""
		def call(fn):
			frame = sys._getframe(1)
			frame.f_locals.setdefault('_applicationSlots', {}).setdefault(message, []).append(fn)
			return fn
		return call

	@staticmethod
	def signal(name = None):
		def call(fn, *args, **kwargs):
			SignalManager.signals[name if type(name) is str else fn.__name__] = Signal(fn)
			def wrapper(obj, *args, **kwargs):
				signalName = name if type(name) is str else fn.__name__
				ctx = obj.context if hasattr(obj, 'context') else Application().pluginContext
				retval = fn(obj, *args, **kwargs)
				SignalManager(ctx).sendSignal(signalName, *args, **kwargs)
				return retval
			return wrapper
		if type(name) is str or name is None:
			# decorator is used like this @signal() or @signal('name')
			return call
		if type(name) is types.FunctionType:
			# decorator is used like this @signal
			return call(name)
		return None

signal = SignalManager.signal
slot = SignalManager.slot
