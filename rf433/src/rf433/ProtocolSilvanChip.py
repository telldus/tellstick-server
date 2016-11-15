 # -*- coding: utf-8 -*-

from Protocol import Protocol
from telldus import Device

class ProtocolSilvanChip(Protocol):

	def methods(self):
		if self.model == 'kp100':
			return (Device.UP | Device.DOWN | Device.STOP | Device.LEARN)
		return (Device.TURNON | Device.TURNOFF | Device.LEARN)

	def stringForMethod(self, method, data=None):
		if self.model == 'kp100':
			preamble = chr(100)+chr(255)+chr(1)+chr(255)+chr(1)+chr(255)+chr(1)+chr(255)+chr(1)+chr(255)+chr(1)+chr(255)+chr(1)+chr(255)+chr(1)+chr(255)+chr(1)+chr(255)+chr(1)+chr(255)+chr(1)+chr(255)+chr(1)+chr(255)+chr(1)+chr(100)

			one = chr(255)+chr(1)+chr(0x2E)+chr(0x2E)
			zero = chr(0x2E)+chr(0xFF)+chr(0x1)+chr(0x2E)
			button = 0
			if method == Device.UP:
				button = 2
			elif method == Device.DOWN:
				button = 8
			elif method == Device.STOP:
				button = 4
			elif method == Device.LEARN:
				button = 1
			else:
				return None
			return self.getString(preamble, one, zero, button)

		elif self.model == 'ecosavers':
			preamble = chr(0x25)+chr(255)+chr(1)+chr(255)+chr(1)+chr(255)+chr(1)+chr(255)+chr(1)+chr(0x25)
			one = chr(0x69)+chr(0x25)
			zero = chr(0x25)+chr(0x69)
			intUnit = self.intParameter('unit', 1, 4)
			button = 0
			if intUnit == 1:
				button = 7
			elif intUnit == 2:
				button = 3
			elif intUnit == 3:
				button = 5
			elif intUnit == 4:
				button = 6

			if method == Device.TURNON or method == Device.LEARN:
				button |= 8
			return self.getString(preamble, one, zero, button)

		S = chr(100)
		L = chr(255)
		LONG = chr(255)+chr(1)+chr(200)

		ONE = LONG + chr(100)
		ZERO = chr(100) + LONG
		strReturn = ''

		io = chr(1)

		strReturn += S+L+io+L+io+L+io+L+io+L+io+L+io+L+io+L+io+L+io+L+io+L+io+L+io+S

		intHouse = self.intParameter('house', 1, 1048575)

		for i in range(19, -1, -1):
			if intHouse & (1 << i):
				strReturn += ONE
			else:
				strReturn += ZERO

		if method == Device.TURNON:
			strReturn += ZERO + ZERO + ONE + ZERO
		elif method == Device.LEARN:
			strReturn += ZERO + ZERO + ZERO + ONE
		elif method == Device.TURNOFF:
			strReturn += ONE + ZERO + ZERO + ZERO
		else:
			return None

		strReturn += ZERO
		return {'S': strReturn}

	def getString(self, preamble, one, zero, button):
		intHouse = self.intParameter('house', 1, 1048575)
		strReturn = preamble

		for i in range(19, -1, -1):
			if intHouse & (1 << i):
				strReturn += one
			else:
				strReturn += zero

		for i in range(3, -1, -1):
			if button & (1 << i):
				strReturn += one
			else:
				strReturn += zero

		strReturn += zero
		return {'S': strReturn}
