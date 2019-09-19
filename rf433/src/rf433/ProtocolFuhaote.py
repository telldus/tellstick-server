 # -*- coding: utf-8 -*-

from .Protocol import Protocol
from telldus import Device

class ProtocolFuhaote(Protocol):
	def methods(self):
		return (Device.TURNON | Device.TURNOFF)

	def stringForMethod(self, method, data=None):
		S = chr(19)
		L = chr(58)
		B0 = S+L+L+S
		B1 = L+S+L+S
		OFF = S+L+S+L+S+L+L+S
		ON  = S+L+L+S+S+L+S+L

		strReturn = ''
		strCode = self.stringParameter('code', '')
		if strCode == '':
			return ''

		# House code
		for i in range(5):
			if strCode[i:i+1] == '0':
				strReturn = strReturn + B0
			elif strCode[i:i+1] == '1':
				strReturn = strReturn + B1
		# Unit code
		for i in range(5, 10):
			if strCode[i:i+1] == '0':
				strReturn = strReturn + B0
			elif strCode[i:i+1] == '1':
				strReturn = strReturn + S+L+S+L

		if method == Device.TURNON:
			strReturn = strReturn + ON
		elif method == Device.TURNOFF:
			strReturn =  strReturn + OFF
		else:
			return ''

		strReturn = strReturn + S
		return {'S': strReturn}
