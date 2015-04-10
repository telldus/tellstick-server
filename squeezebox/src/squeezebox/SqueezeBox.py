# -*- coding: utf-8 -*-

from base import Plugin
from telldus import DeviceManager, Device
from pylms.server import Server
import logging

class Player(Device):
	def __init__(self, player):
		super(Player,self).__init__()
		self.p = player
		self.setName(player.get_name())
		if player.get_power_state():
			self.setState(Device.TURNON)
		else:
			self.setState(Device.TURNOFF)

	def _command(self, action, value, success, failure):
		if action == Device.TURNON:
			self.p.set_power_state(True)
			self.p.play()
			success()
		elif action == Device.TURNOFF:
			self.p.set_power_state(False)
			success()
		else:
			failure(0)

	def localId(self):
		return self.p.get_ref()

	def typeString(self):
		return 'squeezebox'

	def methods(self):
		return Device.TURNON | Device.TURNOFF

class SqueezeBox(Plugin):
	def __init__(self):
		self.deviceManager = DeviceManager(self.context)
		self.sc = Server(hostname='192.168.0.3')
		try:
			self.sc.connect()
		except:
			logger.error("Cannot connect to squeezebox server")
			return
		for player in self.sc.players:
			self.deviceManager.addDevice(Player(player))
		self.deviceManager.finishedLoading('squeezebox')
