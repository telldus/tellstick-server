# -*- coding: utf-8 -*-

# Board config for TellStick ZNet Pro
import os, random, time
from datetime import datetime, timedelta

class Board(object):
	@staticmethod
	def configDir():
		return '/etc'

	@staticmethod
	def gpioConfig():
		return {
			'zwave:reset': {
				'type': 'gpio',
				'port': '12',
			},
		}

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
	def firmwareDownloadDir():
		return '/var/firmware'

	@staticmethod
	def doUpgradeImage(type, path):
		if type == 'firmware':
			os.rename(path, '/var/firmware/core-image-tellstick-znet.img')
		elif type == 'firmware':
			os.rename(path, '/var/firmware/uImage')
		else:
			return
		starttime = datetime.utcnow().replace(hour=0,minute=0,second=0,microsecond=0)
		if datetime.utcnow() > (starttime + timedelta(hours=4)):
			starttime = starttime + timedelta(days=1)
		reboottime = starttime + timedelta(minutes=random.randint(0,240))
		while datetime.utcnow() < reboottime:
			time.sleep(300)
		os.system("/sbin/reboot")
