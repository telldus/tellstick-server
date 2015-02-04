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
		return '/dev/ttyACM0'

	@staticmethod
	def product():
		return 'tellstick-znet-offline'

	@staticmethod
	def hw():
		return 'el-mini'

	@staticmethod
	def firmwareDownloadDir():
		return '/tmp'
