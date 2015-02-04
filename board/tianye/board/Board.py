# -*- coding: utf-8 -*-

# Board config for TellStick ZNet Pro

class Board(object):
	@staticmethod
	def configDir():
		return '/etc'

	@staticmethod
	def liveServer():
		return 'api.telldus.com'

	@staticmethod
	def rf433Port():
		return '/dev/ttyO2'

	@staticmethod
	def zwavePort():
		return '/dev/ttyO5'

	@staticmethod
	def product():
		return 'tellstick-znet'

	@staticmethod
	def hw():
		return '1'

	@staticmethod
	def firmwareDownloadDir();
		return '/var/firmware'
