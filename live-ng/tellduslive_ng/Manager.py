# -*- coding: utf-8 -*-

from base import Application, Plugin
from .Connection import Connection

__name__ = 'tellduslive-ng'  # pylint: disable=W0622

class Manager(Plugin):
	def __init__(self):
		self.connection = Connection()
		Application().registerShutdown(self.connection.shutdown)
