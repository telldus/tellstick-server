 # -*- coding: utf-8 -*-

from Protocol import Protocol
from telldus import Device

class ProtocolBrateck(Protocol):
	def methods(self):
		return (Device.UP | Device.DOWN | Device.STOP)

	def stringForMethod(self, method, data=None):
		S = '!'
		L = 'V'
		B1 = L+S+L+S
		BX = S+L+L+S
		B0 = S+L+S+L
		BUP = L+S+L+S+S+L+S+L+S+L+S+L+S+L+S+L+S
		BSTOP = S+L+S+L+L+S+L+S+S+L+S+L+S+L+S+L+S
		BDOWN = S+L+S+L+S+L+S+L+S+L+S+L+L+S+L+S+S

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
