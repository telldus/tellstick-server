# -*- coding: utf-8 -*-

# Board config for TellStick ZNet light
import os

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
		with open('/tmp/sysinfo/board_name') as f:
			return f.read().strip()

	@staticmethod
	def firmwareDownloadDir():
		return '/tmp'

	@staticmethod
	def doUpgradeImage(type, path):
		if type == 'firmware':
			os.system("/sbin/sysupgrade %s" % path)
