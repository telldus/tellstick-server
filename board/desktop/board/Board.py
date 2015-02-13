# -*- coding: utf-8 -*-

# Board config for desktop

import os

class Board(object):
	@staticmethod
	def configDir():
		return os.environ['HOME'] + '/.config/Telldus'

	@staticmethod
	def gpioConfig():
		return {
			'status:green': {'type': 'none'},
			'status:red': {'type': 'none'},
		}

	@staticmethod
	def liveServer():
		return 'api.telldus.net'

	@staticmethod
	def rf433Port():
		return '/dev/ttyUSB1'

	@staticmethod
	def zwavePort():
		return '/dev/ttyUSB0'
