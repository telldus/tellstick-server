 # -*- coding: utf-8 -*-

from Protocol import ProtocolArctech

class ProtocolWaveman(ProtocolArctech):

	def stringForMethod(self, method, data=None):
		return self.stringForCodeSwitch(method)

	def offCode(self):
		return '$k$k$k$k$k$k$k$k$k'
