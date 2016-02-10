# -*- coding: utf-8 -*-

# Board config for OpenWRT-based boards
import os

class Board(object):
	@staticmethod
	def configDir():
		return '/etc'

	@staticmethod
	def firmwareVersion():
		with open('/etc/builddate') as f:
			return f.readline().strip()

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
	def luaScriptPath():
		return '/usr/lib/telldus/scripts/lua'

	@staticmethod
	def rf433Port():
		return '/dev/ttyUSB0'

	@staticmethod
	def zwavePort():
		return '/dev/ttyACM0'

	@staticmethod
	def secret():
		cfgs = {
			'tellstick-znet-lite': {'part': '/dev/mtd0', 'offset': 0x1FC20},
			'tellstick-znet-fika': {'part': '/dev/mtd2', 'offset': 0x80},
		}
		if Board.hw() not in cfgs:
			return ''
		cfg = cfgs[Board.hw()]
		with open(cfg['part'], 'rb') as f:
			f.seek(cfg['offset'])
			return f.read(10)
		return ''

	@staticmethod
	def product():
		# This might change in the future if we have multiple hardwares for one product.
		return Board.hw()

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
