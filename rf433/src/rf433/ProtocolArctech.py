 # -*- coding: utf-8 -*-

from telldus import Device
from .Protocol import Protocol

class ProtocolArctech(Protocol):
	def deviceType(self):
		models = {
			'selflearning-switch:nexa-dusk': Device.TYPE_ON_OFF_SENSOR,
			'selflearning-switch:nexa-magnet': Device.TYPE_DOOR_WINDOW,
			'selflearning-switch:nexa-pir': Device.TYPE_MOTION,
			'selflearning-switch:nexa-remote': Device.TYPE_REMOTE_CONTROL,
			'selflearning-switch:proove-magnet': Device.TYPE_DOOR_WINDOW,
			'selflearning-switch:proove-pir': Device.TYPE_MOTION,
			'selflearning-switch:proove-remote': Device.TYPE_REMOTE_CONTROL,
			'selflearning-switch:smartwares-dusk': Device.TYPE_ON_OFF_SENSOR,
			'selflearning-switch:smartwares-magnet': Device.TYPE_DOOR_WINDOW,
			'selflearning-switch:smartwares-pir': Device.TYPE_MOTION,
			'selflearning-switch:smartwares-remote': Device.TYPE_REMOTE_CONTROL,
			'selflearning-switch:telldus-magnet': Device.TYPE_DOOR_WINDOW,
			'selflearning-switch:telldus-pir': Device.TYPE_MOTION,
			'selflearning-switch:telldus-remote': Device.TYPE_REMOTE_CONTROL,
		}
		if self.fullModel in models:
			return models[self.fullModel]
		return super(ProtocolArctech, self).deviceType()

	def methods(self):
		if self.model == 'codeswitch':
			return (Device.TURNON | Device.TURNOFF)
		elif self.model == 'selflearning-switch':
			return (Device.TURNON | Device.TURNOFF | Device.LEARN)
		elif self.model == 'selflearning-dimmer':
			return (Device.TURNON | Device.TURNOFF | Device.DIM | Device.LEARN)
		elif self.model == 'selflearning-bell':
			return (Device.BELL | Device.LEARN)
		elif self.model == 'bell':
			return Device.BELL
		return 0

	def stringForMethod(self, method, data=None):
		if self.model == 'codeswitch':
			return self.stringForCodeSwitch(method)
		elif self.model == 'bell':
			return self.stringForBell()
		elif self.model == 'selflearning-bell':
			return self.stringForSelflearning(method, data, 1)

		if method == Device.TURNON and self.model == 'selflearning-dimmer':
			# Workaround for not letting a dimmer do into "dimming mode"
			return self.stringForSelflearning(Device.DIM, 255)
		return self.stringForSelflearning(method, data)

	def stringForBell(self):
		strReturn = ''

		house = self.stringParameter('house', 'A')
		intHouse = ord(house[0]) - ord('A')
		strReturn = strReturn + self.codeSwitchTuple(intHouse)
		strReturn = strReturn + '$kk$$kk$$kk$$k$k'  # Unit 7
		strReturn = strReturn + '$kk$$kk$$kk$$kk$$k'  # Bell
		return {'S': strReturn}

	def stringForCodeSwitch(self, method):
		strHouse = self.stringParameter('house', 'A')
		intHouse = ord(strHouse[0]) - ord('A')
		strReturn = self.codeSwitchTuple(intHouse)
		strReturn = strReturn + self.codeSwitchTuple(self.intParameter('unit', 1, 16)-1)

		if method == Device.TURNON:
			strReturn = strReturn + '$k$k$kk$$kk$$kk$$k'
		elif method == Device.TURNOFF:
			strReturn = strReturn + self.offCode()
		else:
			return None
		return {'S': strReturn}

	def stringForSelflearning(self, method, level, group=0):
		intHouse = self.intParameter('house', 1, 67108863)
		intCode = self.intParameter('unit', 1, 16)-1
		if method == Device.DIM and level == 0:
			method = Device.TURNOFF
		return self.stringSelflearningForCode(intHouse, intCode, method, level, group)

	@staticmethod
	def codeSwitchTuple(intCode):
		strReturn = ''
		for __i in range(4):
			if intCode & 1:  # Convert 1
				strReturn = strReturn + '$kk$'
			else:  # Convert 0
				strReturn = strReturn + '$k$k'
			intCode = intCode >> 1
		return strReturn

	@staticmethod
	def offCode():
		return '$k$k$kk$$kk$$k$k$k'

	@staticmethod
	def stringSelflearningForCode(intHouse, intCode, method, level, group):
		retval = {}
		SHORT = chr(24)  # pylint: disable=C0103
		LONG = chr(127)  # pylint: disable=C0103

		ONE = SHORT + LONG + SHORT + SHORT  # pylint: disable=C0103
		ZERO = SHORT + SHORT + SHORT + LONG  # pylint: disable=C0103

		code = SHORT + chr(255)

		for i in range(25, -1, -1):
			if intHouse & (1 << i):
				code = code + ONE
			else:
				code = code + ZERO

		if group == 1:
			code = code + ONE  # Group (for selflearning bell)
		else:
			code = code + ZERO  # Group

		# On/off
		if method == Device.DIM:
			code = code + SHORT + SHORT + SHORT + SHORT
		elif method == Device.TURNOFF:
			code = code  + ZERO
		elif method == Device.TURNON or method == Device.BELL:
			code = code + ONE
		elif method == Device.LEARN:
			code = code + ONE
			#retval['R'] = 25
		else:
			return None

		for i in range(3, -1, -1):
			if intCode & (1 << i):
				code = code + ONE
			else:
				code = code + ZERO

		if method == Device.DIM:
			newLevel = level/16
			for i in range(3, -1, -1):
				if newLevel & (1 << i):
					code = code + ONE
				else:
					code = code + ZERO

		code = code + SHORT
		retval['S'] = code
		return retval

	@staticmethod
	def decodeData(data):
		if 'model' not in data or 'data' not in data:
			return None
		if data['model'] == 'selflearning':
			return ProtocolArctech.decodeDataSelflearning(data)
		if data['model'] == 'codeswitch':
			return ProtocolArctech.decodeDataCodeSwitch(data)
		return None

	@staticmethod
	def decodeDataSelflearning(data):
		value = int(data['data'], 16)

		house = (value & 0xFFFFFFC0) >> 6
		group = (value & 0x20) >> 5
		# methodCode = (value & 0x10) >> 4
		unit = (value & 0xF)
		unit = unit+1

		if house < 1 or house > 67108863 or unit < 1 or unit > 16:
			# not arctech selflearning
			return None

		method = 0
		if Protocol.checkBit(value, 4):
			method = Device.TURNON
		else:
			method = Device.TURNOFF

		retval = {}
		retval['class'] = 'command'
		retval['protocol'] = 'arctech'
		retval['model'] = 'selflearning'
		retval['house'] = str(house)
		retval['unit'] = str(unit)
		retval['group'] = group
		retval['method'] = method
		return retval

	@staticmethod
	def decodeDataCodeSwitch(data):
		value = int(data['data'], 16)
		methodCode = (value & 0xF00) >> 8
		unit = (value & 0xF0) >> 4
		house = (value & 0xF)

		method = 0
		if methodCode == 6:
			method = Device.TURNOFF
		elif methodCode == 14:
			method = Device.TURNON
		elif methodCode == 15:
			method = Device.BELL
		else:
			return None

		houseString = chr(ord('A') + house)
		unitString = str(unit + 1)
		retval = {}
		retval['class'] = 'command'
		retval['protocol'] = 'arctech'
		retval['model'] = 'codeswitch'
		retval['house'] = houseString
		retval['unit'] = unitString
		retval['method'] = method
		return retval
