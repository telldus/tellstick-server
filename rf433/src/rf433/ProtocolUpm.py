 # -*- coding: utf-8 -*-

from telldus import Device
from .Protocol import Protocol

class ProtocolUpm(Protocol):

	@staticmethod
	def methods():
		return Device.TURNON | Device.TURNOFF

	# pylint: disable=C0103
	def stringForMethod(self, method, data=None):
		del data
		S = ';'
		L = '~'
		STARTq = S
		B1 = L+S
		B0 = S+L
		intUnit = self.intParameter('unit', 1, 4)-1
		strReturn = ''
		code = self.intParameter('house', 0, 4095)
		for i in range(12):
			if code & 1:
				strReturn = B1 + strReturn
			else:
				strReturn = B0 + strReturn
			code >>= 1
		strReturn = START + strReturn  # Startcode, first
		code = 0
		if method == Device.TURNON:
			code += 2
		elif method != Device.TURNOFF:
			return None

		code <<= 2
		code += intUnit
		check1 = 0
		check2 = 0
		for i in range(6):
			if code & 1:
				if i % 2 == 0:
					check1 += 1
				else:
					check2 += 1
			if code & 1:
				strReturn += B1
			else:
				strReturn += B0
			code >>= 1

		if check1 % 2 == 0:
			strReturn += B0
		else:
			strReturn += B1

		if check2 % 2 == 0:
			strReturn += B0
		else:
			strReturn += B1

		return {'S': strReturn}
