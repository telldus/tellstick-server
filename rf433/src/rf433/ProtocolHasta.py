 # -*- coding: utf-8 -*-

from Protocol import Protocol
from telldus import Device

class ProtocolHasta(Protocol):
	def methods(self):
		return (Device.UP | Device.DOWN | Device.STOP | Device.LEARN)

	def stringForMethod(self, method, data=None):
		if self.model == 'selflearningv2':
			return self.stringForMethodV2(method)
		return self.stringForMethodV1(method)

	def stringForMethodV1(self, method):
		house = self.intParameter('house', 1, 65536)
		unit = self.intParameter('unit', 1, 15)
		repeat = 10

		# Preample
		strReturn  = chr(255) + chr(1) + chr(208)
		strReturn = strReturn + chr(160)

		strReturn = strReturn + ProtocolHasta.convertByteV1(house&0xFF)
		strReturn = strReturn + ProtocolHasta.convertByteV1((house>>8)&0xFF)

		byte = unit&0x0F

		if method == Device.UP:
			byte = byte | 0x00
		elif method == Device.DOWN:
			byte = byte | 0x10
		elif method == Device.STOP:
			byte = byte | 0x50
		elif method == Device.LEARN:
			byte = byte | 0x40  # Confirm

		strReturn = strReturn + ProtocolHasta.convertByteV1(byte)
		strReturn = strReturn + ProtocolHasta.convertByteV1(0)
		strReturn = strReturn + ProtocolHasta.convertByteV1(0)

		# Remove the last pulse
		strReturn = strReturn[:-1]

		return {'S': strReturn, 'R': repeat, 'P': 25}

	@staticmethod
	def convertByteV1(byte):
		retval = ''
		for i in range(8):
			if byte & 1:
				retval = retval + chr(32) + chr(17)
			else:
				retval = retval + chr(17) + chr(32)
			byte = byte >> 1
		return retval

	def stringForMethodV2(self, method):
		house = self.intParameter('house', 1, 65536)
		unit = self.intParameter('unit', 1, 15)
		repeat = 10

		# Preample
		strReturn = chr(255) + chr(1) + chr(208)
		strReturn = strReturn + chr(250)
		strReturn = strReturn + chr(155)
		strReturn = strReturn + chr(35)

		strReturn = strReturn + ProtocolHasta.convertByteV2((house>>8)&0xFF)
		csum = ((house>>8)&0xFF)
		strReturn = strReturn + ProtocolHasta.convertByteV2(house&0xFF)
		csum = csum + (house&0xFF)

		byte = unit&0x0F

		if method == Device.UP:
			byte = byte | 0xC0
		elif method == Device.DOWN:
			byte = byte | 0x10
		elif method == Device.STOP:
			byte = byte | 0x50
		elif method == Device.LEARN:
			byte = byte | 0x40  # Confirm

		strReturn = strReturn + ProtocolHasta.convertByteV2(byte)
		csum = csum + byte

		strReturn = strReturn + ProtocolHasta.convertByteV2(0x01)  # unknown
		csum = csum + 0x01

		checksum = ((int(csum/256)+1)*256+1) - csum

		strReturn = strReturn + ProtocolHasta.convertByteV2(checksum)
		strReturn = strReturn + chr(66) + chr(35)

		return {'S': strReturn, 'R': repeat, 'P': 0}

	@staticmethod
	def convertByteV2(byte):
		retval = ''
		for i in range(8):
			if byte & 1:
				retval = retval + chr(66) + chr(35)
			else:
				retval = retval + chr(35) + chr(66)
			byte = byte >> 1
		return retval
