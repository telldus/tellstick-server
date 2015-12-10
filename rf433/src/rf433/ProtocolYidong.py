 # -*- coding: utf-8 -*-

from Protocol import ProtocolSartano

class ProtocolYidong(ProtocolSartano):

	def stringForMethod(self, method, data=None):
		intCode = self.intParameter('unit', 1, 4)
		codes = {
			1: '0010',
			2: '0001',
			3: '0100',
			4: '1000'
		}
		return self.stringForCode('111%s110' % codes[intCode], method)
