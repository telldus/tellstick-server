# -*- coding: utf-8 -*-

from ProtocolFineoffset import *
from ProtocolMandolyn import *
from ProtocolOregon import *

class Protocol():
	def __init__(self, protocol, model):
		self.protocol = protocol
		index = model.find(':')
		if (index >= 0):
			self.model = model[0:index]
		else:
			self.model = model

	def convertToRaw(self, name, value):
		if (self.protocol == 'arctech' or self.protocol == 'waveman'):
			if (self.model == 'codeswitch'):
				if (name == 'house'):
					return ord(value[0])-ord('A')
				elif (name == 'unit'):
					return int(value)
			else:
				return value #this might be 'E', ' ' or 'H' too

		if (self.protocol == 'x10'):
			if (name == 'house'):
				return ord(value[0])-ord('A')
			elif (name == 'unit'):
				return int(value)
		return value

	def decodeData(self, data):
		pass

	@staticmethod
	def methodsForProtocol(protocol, model):
		if (protocol == 'arctech'):
			if (model == 'codeswitch'):
				return Protocol.TELLSTICK_TURNON | Protocol.TELLSTICK_TURNOFF
			if (model == 'selflearning'):
				return Protocol.TELLSTICK_TURNON | Protocol.TELLSTICK_TURNOFF
			if (model == 'selflearning-bell'):
				return Protocol.TELLSTICK_BELL
		if (protocol == 'comen'):
				return Protocol.TELLSTICK_TURNON | Protocol.TELLSTICK_TURNOFF
		if (protocol == 'everflourish'):
				return Protocol.TELLSTICK_TURNON | Protocol.TELLSTICK_TURNOFF
		if (protocol == 'sartano'):
				return Protocol.TELLSTICK_TURNON | Protocol.TELLSTICK_TURNOFF
		if (protocol == 'waveman'):
				return Protocol.TELLSTICK_TURNON | Protocol.TELLSTICK_TURNOFF
		if (protocol == 'x10'):
				return Protocol.TELLSTICK_TURNON | Protocol.TELLSTICK_TURNOFF
		if (protocol == 'hasta'):
				return Protocol.TELLSTICK_UP | Protocol.TELLSTICK_DOWN | Protocol.TELLSTICK_STOP
		return 0

	@staticmethod
	def methodStringToInt(methodString):
		if (methodString == 'turnon'):
			return Protocol.TELLSTICK_TURNON
		elif (methodString == 'turnoff'):
			return Protocol.TELLSTICK_TURNOFF
		elif (methodString == 'dim'):
			return Protocol.TELLSTICK_DIM
		return 0

	@staticmethod
	def parametersForProtocol(protocol, model):
		if (protocol == 'arctech' or protocol == 'waveman' or protocol == 'comen'):
			return ['house', 'unit']
		if (protocol == 'everflourish'):
			return ['house', 'unit']
		if (protocol == 'sartano'):
			return ['code']
		if (protocol == 'x10'):
			return ['house', 'unit']
		if (protocol == 'hasta'):
			return ['house', 'unit']
		return []

	@staticmethod
	def protocolInstance(protocol):
		if (protocol == 'fineoffset'):
			return ProtocolFineoffset()
		if (protocol == 'mandolyn'):
			return ProtocolMandolyn()
		if (protocol == 'oregon'):
			return ProtocolOregon()
		return None
