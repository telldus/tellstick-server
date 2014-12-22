 # -*- coding: utf-8 -*-

from Protocol import Protocol
from telldus import Device
import logging

class ProtocolArctech(Protocol):
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

		if method == 'turnon' and self.model == 'selflearning-dimmer':
			# Workaround for not letting a dimmer do into "dimming mode"
			return self.stringForSelflearning('dim', 255)
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

		if method == 'turnon':
			strReturn = strReturn + '$k$k$kk$$kk$$kk$$k'
		elif method == 'turnoff':
			strReturn = strReturn + '$k$k$kk$$kk$$k$k$k'
		else:
			return None
		return {'S': strReturn}

	def stringForSelflearning(self, method, level, group=0):
		intHouse = self.intParameter('house', 1, 67108863)
		intCode = self.intParameter('unit', 1, 16)-1
		if method == 'dim' and level == 0:
			method = 'turnoff'
		return self.stringSelflearningForCode(intHouse, intCode, method, level, group)

	def codeSwitchTuple(self, intCode):
		strReturn = ''
		for i in range(4):
			if intCode & 1:  # Convert 1
				strReturn = strReturn + '$kk$'
			else:  # Convert 0
				strReturn = strReturn + '$k$k'
			intCode = intCode >> 1
		return strReturn

	def stringSelflearningForCode(self, intHouse, intCode, method, level, group):
		retval = {}
		SHORT = chr(24)
		LONG = chr(127)

		ONE = SHORT + LONG + SHORT + SHORT
		ZERO = SHORT + SHORT + SHORT + LONG

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
		if method == 'dim':
			code = code + SHORT + SHORT + SHORT + SHORT
		elif method == 'turnoff':
			code = code  + ZERO
		elif method == 'turnon' or method == 'bell':
			code = code + ONE
		elif method == 'learn':
			code = code + ONE
			retval['R'] = 25
		else:
			return None

		for i in range(3, -1, -1):
			if intCode & (1 << i):
				code = code + ONE
			else:
				code = code + ZERO

		if method == 'dim':
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
		if data['model'] == 'codeswitch':
			return ProtocolArctech.decodeDataCodeSwitch(data)
		return None

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
