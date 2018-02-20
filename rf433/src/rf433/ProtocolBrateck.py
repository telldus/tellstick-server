 # -*- coding: utf-8 -*-

from telldus import Device
from .Protocol import Protocol

class ProtocolBrateck(Protocol):
	def methods(self):
		return (Device.UP | Device.DOWN | Device.STOP)

	def stringForMethod(self, method, __data=None):
		S = '!'  # pylint: disable=C0103
		L = 'V'  # pylint: disable=C0103
		B1 = L+S+L+S  # pylint: disable=C0103
		BX = S+L+L+S  # pylint: disable=C0103
		B0 = S+L+S+L  # pylint: disable=C0103
		BUP = L+S+L+S+S+L+S+L+S+L+S+L+S+L+S+L+S  # pylint: disable=C0103
		BSTOP = S+L+S+L+L+S+L+S+S+L+S+L+S+L+S+L+S  # pylint: disable=C0103
		BDOWN = S+L+S+L+S+L+S+L+S+L+S+L+L+S+L+S+S  # pylint: disable=C0103

		strReturn = ''
		strHouse = self.stringParameter('house', '')
		if strHouse == '':
			return ''

		for i in strHouse:
			if i == '1':
				strReturn = B1+strReturn
			elif i == '-':
				strReturn = BX+strReturn
			elif i == '0':
				strReturn = B0+strReturn

		if method == Device.UP:
			strReturn += BUP
		elif method == Device.DOWN:
			strReturn += BDOWN
		elif method == Device.STOP:
			strReturn += BSTOP
		else:
			return None
		return {'S': strReturn}
