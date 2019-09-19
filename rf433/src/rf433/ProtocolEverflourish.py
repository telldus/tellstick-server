 # -*- coding: utf-8 -*-

from .Protocol import Protocol
from telldus import Device

class ProtocolEverflourish(Protocol):
	def methods(self):
		return (Device.TURNON | Device.TURNOFF | Device.LEARN)

	def stringForMethod(self, method, data=None):
		deviceCode = self.intParameter('house', 0, 16383)
		intCode = self.intParameter('unit', 1, 4)-1

		if method == Device.TURNON:
			action = 15
		elif method == Device.TURNOFF:
			action = 0
		elif method == Device.LEARN:
			action = 10
		else:
			return ''

		s = chr(60)
		l = chr(114)

		ssss = s+s+s+s
		sssl = s+s+s+l  # 0
		slss = s+l+s+s  # 1

		bits = [sssl,slss]

		deviceCode = (deviceCode << 2) | intCode

		check = ProtocolEverflourish.calculateChecksum(deviceCode)

		strCode = s+s+s+s+s+s+s+s

		for i in range(15, -1, -1):
			strCode = strCode + bits[(deviceCode>>i)&0x01]
		for i in range(3, -1, -1):
			strCode = strCode + bits[(check>>i)&0x01]
		for i in range(3, -1, -1):
			strCode = strCode + bits[(action>>i)&0x01]

		strCode = strCode + ssss

		return {'S': strCode}

	@staticmethod
	def calculateChecksum(x):
		bits = [
			0xf, 0xa, 0x7, 0xe,
			0xf, 0xd, 0x9, 0x1,
			0x1, 0x2, 0x4, 0x8,
			0x3, 0x6, 0xc, 0xb
		]
		bit = 1
		res = 0x5

		if (x&0x3) == 3:
			lo = x & 0x00ff
			hi = x & 0xff00
			lo += 4
			if lo > 0x100:
				lo = 0x12
			x = lo | hi

		for i in range(16):
			if x&bit:
				res = res ^ bits[i]
			bit = bit << 1
		return res
