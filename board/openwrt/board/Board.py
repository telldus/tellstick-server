# -*- coding: utf-8 -*-

# Board config for OpenWRT-based boards
import os

class Board(object):
	cfgs = {
		'tellstick-znet-lite': {
			'secret': {'part': '/dev/mtd0', 'offset': 0x1FC20},
			'433': '/dev/ttyUSB0',
			'z-wave': '/dev/ttyACM0',
		},
		'tellstick-znet-fika': {
			'secret': {'part': '/dev/mtd2', 'offset': 0x80},
			'433': '/dev/ttyUSB0',
			'z-wave': '/dev/ttyACM0',
		},
	}

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
		return Board.__cfg('433')

	@staticmethod
	def zwavePort():
		return Board.__cfg('z-wave')

	@staticmethod
	def secret():
		cfg = Board.__cfg('secret')
		if cfg is None:
			return ''
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

	@staticmethod
	def __cfg(name, default = None):
		hw = Board.hw()
		if hw not in Board.cfgs:
			return default
		cfg = Board.cfgs[hw]
		if name not in cfg:
			return default
		return cfg[name]
