 # -*- coding: utf-8 -*-

from Protocol import Protocol
from telldus import Device
from math import ceil

class ProtocolKangtai(Protocol):
	def methods(self):
		if self.model == 'selflearning-dimmer':
			return (Device.TURNON | Device.TURNOFF | Device.LEARN | Device.DIM)
		return (Device.TURNON | Device.TURNOFF | Device.LEARN)

	def stringForMethod(self, method, data=None):
		if self.model == 'selflearning-dimmer':
			return self.stringForMethodDim(method, data)
		else:
			return self.stringForMethodOnOff(method, data)

	def stringForMethodOnOff(self, method, data):
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


	def stringForMethodDim(self, method, data):
		ZERO = chr(50)+chr(150)
		ONE = chr(150)+chr(50)

		intHouse = self.intParameter('house', 1, 65535)
		intCode = self.intParameter('unit', 1, 126)  # 0 = Group, 1111111 = Test, factory use only

		# Preamble
		strReturn = chr(50)  # 500 us
		strReturn = strReturn + chr(255)+chr(1)+chr(255)+chr(1)+chr(190)  # 7 ms

		binNoCrypt = intHouse  # address (house)
		binNoCrypt = binNoCrypt << 8  # go to the "function" byte

		# first 4 bits 0 or reserved at the moment
		# data = dim-level 0-255
		if (data == 0 and method == Device.DIM) or method == Device.TURNOFF:
			binNoCrypt = binNoCrypt | 12  # off
		elif method == Device.LEARN:
			# learn, send "on"
			# "On" = start the dimmer at the previous level, but two "on":s in a row make it dim up and down, so ignore that feature
			binNoCrypt = binNoCrypt | 11
		elif method == Device.TURNON:
			binNoCrypt = binNoCrypt | 8  # max level
		else:
			level = int(ceil(data / 32))
			binNoCrypt = binNoCrypt | level

		binNoCrypt = binNoCrypt << 1  # shift for seq (toggles between 1 and 0, we don't know previous value, so always send 0, then it will work in at least every other transmit)
		binNoCrypt = binNoCrypt << 7  # shift to make room for unit
		binNoCrypt = binNoCrypt | intCode

		g7 = ((binNoCrypt & 0xF0000000) >> 28)
		g6 = ((binNoCrypt & 0x0F000000) >> 24)
		g5 = ((binNoCrypt & 0x00F00000) >> 20)
		g4 = ((binNoCrypt & 0x000F0000) >> 16)
		g3 = ((binNoCrypt & 0x0000F000) >> 12)
		g2 = ((binNoCrypt & 0x00000F00) >> 8)
		g1 = ((binNoCrypt & 0x000000F0) >> 4)
		g0 = (binNoCrypt & 0x0000000F)

		enctable1 = [1, 8, 12, 5, 7, 10, 3, 15, 2, 11, 0, 14, 4, 9, 13, 6]
		enctable2 = [2, 9, 13, 6, 8, 11, 4, 0, 3, 12, 1, 15, 5, 10, 14, 7]

		k = {}
		k[0] = enctable1[g0];
		k[1] = enctable1[(g1^k[0])]
		k[2] = enctable1[(g2^k[1])]
		k[3] = enctable1[(g3^k[2])]
		k[4] = enctable1[(g4^k[3])]
		k[5] = enctable1[(g5^k[4])]
		k[6] = enctable1[(g6^k[5])]
		k[7] = enctable1[(g7^k[6])]

		m = {}
		m[0] = enctable2[k[0]]
		m[1] = enctable2[(k[1]^m[0])]
		m[2] = enctable2[(k[2]^m[1])]
		m[3] = enctable2[(k[3]^m[2])]
		m[4] = enctable2[(k[4]^m[3])]
		m[5] = enctable2[(k[5]^m[4])]
		m[6] = enctable2[(k[6]^m[5])]
		m[7] = enctable2[(k[7]^m[6])]

		for i in range(7, -1, -1):
			for j in range(3, -1, -1):
				strReturn += ZERO if ((m[i] >> j) & 1) == 0 else ONE

		retval = {'S': strReturn, 'P': 0}
		if method == Device.LEARN:
			retval['R'] = 50  # don't know if this is necessary really
		return retval
