 # -*- coding: utf-8 -*-

from ProtocolArctech import ProtocolArctech
from telldus import Device

class ProtocolComen(ProtocolArctech):
	def methods(self):
		return (Device.TURNON | Device.TURNOFF | Device.LEARN)

	def intParameter(self, name, min, max):
		if name == 'house':
			house = super(ProtocolComen,self).intParameter('house', 1, 16777215)
			# The last two bits must be hardcoded
			house = house << 2
			house = house + 2
			return house
		return super(ProtocolComen,self).intParameter(name, min, max)

	@staticmethod
	def decodeData(data):
		if 'data' not in data:
			return None
		msg = None
		value = int(data['data'], 16)

		house = (value & 0xFFFFFFC0) >> 6
		if house & 0x3 != 0x2:
			# Not Comen
			return None
		house = house >> 2
		group = (value & 0x20) >> 5
		methodCode = (value & 0x10) >> 4
		unit = (value & 0xF)
		unit = unit+1
		if unit < 1 or unit > 16:
			# Not Comen
			return None

		method = 0
		if ProtocolComen.checkBit(value, 4):
			method = Device.TURNON
		else:
			method = Device.TURNOFF

		return {
			'class': 'command',
			'protocol': 'comen',
			'model': 'selflearning',
			'house': str(house),
			'unit': str(unit),
			'method': method,
		}
