 # -*- coding: utf-8 -*-

from Protocol import Protocol
from telldus import Device

class ProtocolKangtai(Protocol):
	def methods(self):
		return (Device.TURNON | Device.TURNOFF | Device.LEARN)

	def stringForMethod(self, method, data=None):
		ZERO = chr(37)+chr(112)
		ONE = chr(112)+chr(37)

		intHouse = self.intParameter('house', 1, 65535)
		intCode = self.intParameter('unit', 1, 30)  # 0 = Group, 11111 = Test, factory use only

		# Preample, type1
		strReturn = chr(38)  # 375 us
		strReturn = strReturn + chr(225)  # 2250 us

		binNoCrypt = intHouse  # address (house)
		binNoCrypt = binNoCrypt << 3  # "count" = 2 bits, then method

		if method != Device.TURNOFF:
			binNoCrypt = binNoCrypt | 1  # method

		binNoCrypt = binNoCrypt << 5  # shift to make room for unit
		binNoCrypt = binNoCrypt | intCode

		g5 = ((binNoCrypt & 0xF00000) >> 20)
		g4 = ((binNoCrypt & 0x0F0000) >> 16)
		g3 = ((binNoCrypt & 0x00F000) >> 12)
		g2 = ((binNoCrypt & 0x000F00) >> 8)
		g1 = ((binNoCrypt & 0x0000F0) >> 4)
		g0 = (binNoCrypt & 0x00000F)

		if (g5 & 2) == 0:
			enctable = [10, 0, 4, 12, 2, 14, 7, 5, 1, 15, 11, 13, 9, 6, 3, 8]
		else:
			enctable = [2, 12, 5, 14, 7, 4, 1, 15, 11, 13, 6, 3, 8, 9, 10, 0]

		k = {}
		k[0] = enctable[g0]
		k[1] = enctable[(g1^k[0])]
		k[2] = enctable[(g2^k[1])]
		k[3] = enctable[(g3^k[2])]
		k[4] = enctable[(g4^k[3])]
		k[5] = g5^9

		for i in range(5, -1, -1):
			for j in range(3, -1, -1):
				if ((k[i] >> j) & 1) == 0:
					strReturn = strReturn + ZERO
				else:
					strReturn = strReturn + ONE

		retval = {'S': strReturn, 'P': 0}
		if method == Device.LEARN:
			retval['R'] = 50  # don't know if this is necessary really
		return retval
