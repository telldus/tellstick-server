# -*- coding: utf-8 -*-

from Application import Application
from Plugin import IInterface, ObserverCollection, Plugin

class ISignalObserver(IInterface):
	"""Implement this IInterface to recieve signals using the decorator :func:`@slot`"""

class SignalManager(Plugin):
	observers = ObserverCollection(ISignalObserver)

	def signal(self, msg, *args, **kwargs):
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
			import sys
			frame = sys._getframe(1)
			frame.f_locals.setdefault('_applicationSlots', {}).setdefault(message, []).append(fn)
			return fn
		return call

slot = SignalManager.slot
