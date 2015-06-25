# -*- coding: utf-8 -*-

from base import Plugin
from telldus import DeviceManager, Device
from ouimeaux.environment import Environment
from threading import Thread
import logging

class WeMoDevice(Device):
	def __init__(self, device):
		super(WeMoDevice,self).__init__()
		self.device = device
		self.setName(device.name)

	def localId(self):
		return self.device.serialnumber

	def typeString(self):
		return 'wemo'

class WeMoSwitch(WeMoDevice):
	def __init__(self, device):
		super(WeMoSwitch,self).__init__(device)

	def _command(self, action, value, success, failure):
		if action == Device.TURNON:
			self.device.on()
			success()
		elif action == Device.TURNOFF:
			self.device.off()
			success()
		else:
			failure(0)

	def methods(self):
		return Device.TURNON | Device.TURNOFF

class WeMoLight(Device):
	def __init__(self, bridge, light):
		super(WeMoLight,self).__init__()
		self.bridge = bridge
		self.light = light
		self.attr = bridge.light_attributes(light)
		self.setName(self.attr['name'])

	def _command(self, action, value, success, failure):
		if action == Device.TURNON:
			dim = 255
			state = 1
		elif action == Device.TURNOFF:
			dim = None
			state = 0
		elif action == Device.DIM:
			dim = value
			state = 1
		else:
			failure(0)
			return
		self.bridge.light_set_state(self.light,state=state,dim=dim)
		success()

	def localId(self):
		return self.attr['devID']

	def typeString(self):
		return 'wemo'

	def methods(self):
		return Device.TURNON | Device.TURNOFF | Device.DIM

class WeMo(Plugin):
	def __init__(self):
		self.devices = {}
		self.deviceManager = DeviceManager(self.context)
		self.env = Environment(
			switch_callback=self.switchFound,
			motion_callback=self.motionFound,
			bridge_callback=self.bridgeFound,
		)
		Thread(target=self.discover).start()

	def addDevice(self, DeviceType, device):
		if device.serialnumber in self.devices:
			return
		d = DeviceType(device)
		self.deviceManager.addDevice(d)
		self.devices[device.serialnumber] = d

	def bridgeFound(self, bridge):
		if bridge.serialnumber in self.devices:
			return
		self.devices[bridge.serialnumber] = bridge
		bridge.bridge_get_lights()
		for light in bridge.Lights:
			d = WeMoLight(bridge, bridge.Lights[light])
			self.deviceManager.addDevice(d)

	def discover(self):
		self.env.start()
		self.env.discover(seconds=5)
		self.deviceManager.finishedLoading('wemo')

	def motionFound(self, motion):
		logging.info("WeMo motion found: %s", motion)
		# TODO(micke): Implement this when we have a sample

	def switchFound(self, switch):
		self.addDevice(WeMoSwitch, switch)
