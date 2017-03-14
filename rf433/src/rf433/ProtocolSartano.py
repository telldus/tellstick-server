 # -*- coding: utf-8 -*-

from Protocol import Protocol
from telldus import Device

class ProtocolSartano(Protocol):

	def methods(self):
		return (Device.TURNON | Device.TURNOFF)

	def stringForMethod(self, method, data=None):
		strCode = self.stringParameter('code', '')
		return ProtocolSartano.stringForCode(strCode, method)

	@staticmethod
	def decodeData(data):
		method = None
		value = int(data['data'], 16)
		totData = 0

		mask = (1<<11)
		for i in range(0,12):
			totData >>= 1
			if (value & mask) == 0:
				totData |= (1<<11)
			mask >>= 1

		code = totData & 0xFFC
		code >>= 2

		method1 = totData & 0x2
		method1 >>= 1

		method2 = totData & 0x1

		if method1 == 0 and method2 == 1:
			method = Device.TURNOFF
		elif method1 == 1 and method2 == 0:
			method = Device.TURNON
		else:
			return None

		if code < 0 or code > 1023 or not method:
			# not sartano
			return None

		returnstring = ""
		mask = (1<<9)
		for i in range(0,10):
			if (code & mask) != 0:
				returnstring = returnstring + "1"
			else:
				returnstring = returnstring + "0"
			mask >>= 1
		retval = {}
		retval['class'] = 'command'
		retval['protocol'] = 'sartano'
		retval['model'] = 'codeswitch'
		retval['code'] = returnstring
		retval['method'] = method
		return retval

	@staticmethod
	def stringForCode(strCode, method):
		strReturn = ''

		for i in strCode:
			if i == '1':
				strReturn = strReturn + '$k$k'
			else:
				strReturn = strReturn + '$kk$'

		if method == Device.TURNON:
			strReturn = strReturn + '$k$k$kk$$k'
		elif method == Device.TURNOFF:
			strReturn = strReturn + '$kk$$k$k$k'
		else:
			return None

		return {'S': strReturn}
