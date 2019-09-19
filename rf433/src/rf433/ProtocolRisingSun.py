 # -*- coding: utf-8 -*-

from .Protocol import Protocol
from telldus import Device

class ProtocolRisingSun(Protocol):
	def methods(self):
		if self.model == 'selflearning':
			return (Device.TURNON | Device.TURNOFF | Device.LEARN)
		return (Device.TURNON | Device.TURNOFF)

	def stringForMethod(self, method, data=None):
		if self.model == 'selflearning':
			return self.stringSelflearning(method)
		return self.stringCodeSwitch(method)

	def stringSelflearning(self, method):
		intHouse = self.intParameter('house', 1, 33554432)-1
		intCode = self.intParameter('unit', 1, 16)-1

		codeOn = [
			'110110', '001110', '100110', '010110',
			'111001', '000101', '101001', '011001',
			'110000', '001000', '100000', '010000',
			'111100', '000010', '101100', '011100'
		]
		codeOff = [
			'111110', '000001', '101110', '011110',
			'110101', '001101', '100101', '010101',
			'111000', '000100', '101000', '011000',
			'110010', '001010', '100010', '010010'
		]
		l = chr(120)
		s = chr(51)

		strCode = '10'
		code = intCode
		code = 0 if code < 0 else code
		code = 15 if code > 15 else code
		if method == Device.TURNON:
			strCode = strCode + codeOn[code]
		elif method == Device.TURNOFF:
			strCode = strCode + codeOff[code]
		elif method == Device.LEARN:
			strCode = strCode + codeOn[code]
		else:
			return None

		house = intHouse
		for i in range(25):
			if house & 1:
				strCode = strCode + '1'
			else:
				strCode = strCode + '0'
			house = house >> 1

		strReturn = ''
		for i in strCode:
			if i == '1':
				strReturn = strReturn + l + s
			else:
				strReturn = strReturn + s + l

		retval = {'S': strReturn, 'P': 5}
		if method == Device.LEARN:
			retval['R'] = 50
		return retval

	def stringCodeSwitch(self, method):
		strReturn = '.e'
		strReturn = strReturn + ProtocolRisingSun.codeSwitchTuple(self.intParameter('house', 1, 4)-1)
		strReturn = strReturn + ProtocolRisingSun.codeSwitchTuple(self.intParameter('unit', 1, 4)-1)
		if method == Device.TURNON:
			strReturn = strReturn + 'e..ee..ee..ee..e'
		elif method == Device.TURNOFF:
			strReturn = strReturn + 'e..ee..ee..e.e.e'
		else:
			return None
		return {'S': strReturn}

	@staticmethod
	def codeSwitchTuple(intToConvert):
		strReturn = ''
		for i in range(4):
			if i == intToConvert:
				strReturn = strReturn + '.e.e'
			else:
				strReturn = strReturn + 'e..e'
		return strReturn
