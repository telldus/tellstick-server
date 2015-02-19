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
