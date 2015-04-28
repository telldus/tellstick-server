# -*- coding: utf-8 -*-

# Board config for OpenWRT-based boards
import os

class Board(object):
	@staticmethod
	def configDir():
		return '/etc'

	@staticmethod
	def gpioConfig():
		return {
			'status:red': {
				'type': 'led',
				'port': 'tellstick:red:status'
			},
			'status:green': {
				'type': 'led',
				'port': 'tellstick:green:status'
			},
			'zwave:reset': {'type': 'none'},
		}

	@staticmethod
	def networkInterface():
		return 'eth0'

	@staticmethod
	def liveServer():
		return 'api.telldus.com'

	@staticmethod
	def rf433Port():
		return '/dev/ttyUSB0'

	@staticmethod
	def zwavePort():
		return '/dev/ttyACM0'

	@staticmethod
	def secret():
		with open('/dev/mtd0', 'rb') as f:
			f.seek(0x1FC20)
			return f.read(10)
		return ''

	@staticmethod
	def product():
		return 'tellstick-znet-lite'

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
