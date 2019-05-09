# -*- coding: utf-8 -*-

# Board config for OpenWRT-based boards
import os
import netifaces

class Board(object):
	cfgs = {
		'tellstick-net-v2': {
			'secret': {'part': '/dev/mtd0', 'offset': 0x1FC20},
			'433': 'hwgrep://1781:0c32',
		},
		'tellstick-znet-lite': {
			'secret': {'part': '/dev/mtd0', 'offset': 0x1FC20},
			'433': '/dev/ttyUSB0',
			'z-wave': '/dev/ttyACM0',
		},
		'tellstick-znet-lite-v2': {
			'secret': {'part': '/dev/mtd0', 'offset': 0x1FC20},
			'433': 'hwgrep://1781:0c32',
			'z-wave': 'hwgrep://0658:0200',
		},
		'tellstick-znet-fika': {
			'secret': {'part': '/dev/mtd2', 'offset': 0x80},
			'433': '/dev/ttyUSB0',
			'z-wave': '/dev/ttyACM0',
		},
	}

	@staticmethod
	def configDir():
		return '/etc/telldus'

	@staticmethod
	def firmwareVersion():
		with open('/etc/builddate') as f:
			return f.readline().strip()

	@staticmethod
	def getMacAddr():
		addrs = netifaces.ifaddresses(Board.networkInterface())
		try:
			mac = addrs[netifaces.AF_LINK][0]['addr']
		except (IndexError, KeyError):
			return ''
		return mac.upper().replace(':', '')

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
			'status:blue': {
				'type': 'led',
				'port': 'tellstick:blue:status'
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
	def pluginPath():
		return '/usr/lib/telldus/plugins'

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
		hw = Board.hw()
		if hw != 'tellstick':
			return hw
		# "tellstick" as hw is a generic hw platform. We need to manually figure out the correct product
		# to upgrade to the correct firmware
		if Board.__readGPIO(26) == '0':
			return 'tellstick-znet-lite-v2'
		return 'tellstick-net-v2'

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
			if Board.hw() == 'tellstick':
				# Force upgrade since the image id won't match when we switch board type
				os.system("/sbin/sysupgrade -F %s" % path)
			else:
				os.system("/sbin/sysupgrade %s" % path)

	@staticmethod
	def __cfg(name, default = None):
		product = Board.product()
		if product not in Board.cfgs:
			return default
		cfg = Board.cfgs[product]
		if name not in cfg:
			return default
		return cfg[name]

	@staticmethod
	def __readGPIO(pin):
		if os.path.exists('/sys/class/gpio/gpio%s' % pin) == False:
			if os.path.exists('/sys/class/gpio/export') == False:
				return None
			# Export the gpio
			with open('/sys/class/gpio/export', 'w') as f:
				f.write(str(pin))
		if os.path.exists('/sys/class/gpio/gpio%s' % pin) == False:
			return None
		with open('/sys/class/gpio/gpio%s/direction' % pin, 'w') as f:
			f.write('in')
		with open('/sys/class/gpio/gpio%s/value' % pin, 'r') as f:
			return f.read().strip()
