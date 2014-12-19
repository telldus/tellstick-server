# -*- coding: utf-8 -*-

# Board config for TellStick ZNet light

class Board(object):
	@staticmethod
	def configDir():
		return '/etc'

	@staticmethod
	def liveServer():
		return 'api.telldus.com'

	@staticmethod
	def zwavePort():
		return '/dev/ttyUSB0'
