# -*- coding: utf-8 -*-

# Board config for desktop

import os, subprocess

class Board(object):
	@staticmethod
	def configDir():
		return os.environ['HOME'] + '/.config/Telldus'

	@staticmethod
	def firmwareVersion():
		return subprocess.check_output(['git', 'describe'])[1:]

	@staticmethod
	def networkInterface():
		return 'eth0'

	@staticmethod
	def gpioConfig():
		return {
			'status:green': {'type': 'none'},
			'status:red': {'type': 'none'},
			'zwave:reset': {'type': 'none'},
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
