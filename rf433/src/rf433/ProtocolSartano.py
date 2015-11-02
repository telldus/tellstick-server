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
