 # -*- coding: utf-8 -*-

from .Protocol import Protocol
from telldus import Device

class ProtocolX10(Protocol):
	HOUSES = [6,0xE,2,0xA,1,9,5,0xD,7,0xF,3,0xB,0,8,4,0xC]

	def methods(self):
		return (Device.TURNON | Device.TURNOFF)

	def stringForMethod(self, method, data=None):
		S = chr(59)
		L = chr(169)
		B0 = S + S
		B1 = S + L
		START_CODE = chr(255)+chr(1)+chr(255)+chr(1)+chr(255)+chr(1)+chr(100)+chr(255)+chr(1)+chr(180)
		STOP_CODE = S

		strReturn = START_CODE
		strComplement = ''

		strHouse = self.stringParameter('house', 'A')
		intHouse = ord(strHouse[0]) - ord('A')
		if intHouse < 0:
			intHouse = 0
		elif intHouse > 15:
			intHouse = 15
		# Translate it
		intHouse = ProtocolX10.HOUSES[intHouse]
		intCode = self.intParameter('unit', 1, 16)-1

		for i in range(4):
			if intHouse & 1:
				strReturn = strReturn + B1
				strComplement = strComplement + B0
			else:
				strReturn = strReturn + B0
				strComplement = strComplement + B1
			intHouse = intHouse >> 1
		strReturn = strReturn + B0
		strComplement = strComplement + B1

		if intCode >= 8:
			strReturn = strReturn + B1
			strComplement = strComplement + B0
		else:
			strReturn = strReturn + B0
			strComplement = strComplement + B1

		strReturn = strReturn + B0
		strComplement = strComplement + B1
		strReturn = strReturn + B0
		strComplement = strComplement + B1

		strReturn = strReturn + strComplement
		strComplement = ''

		strReturn = strReturn + B0
		strComplement = strComplement + B1

		if (intCode >> 2) & 1:  # Bit 2 of intCode
			strReturn = strReturn + B1
			strComplement = strComplement + B0
		else:
			strReturn = strReturn + B0
			strComplement = strComplement + B1

		if method == Device.TURNON:
			strReturn = strReturn + B0
			strComplement = strComplement + B1
		elif method == Device.TURNOFF:
			strReturn = strReturn + B1
			strComplement = strComplement + B0
		else:
			return None

		if intCode & 1:  # Bit 0 of intCode
			strReturn = strReturn + B1
			strComplement = strComplement + B0
		else:
			strReturn = strReturn + B0
			strComplement = strComplement + B1

		if (intCode >> 1) & 1:  # Bit 1 of intCode
			strReturn = strReturn + B1
			strComplement = strComplement + B0
		else:
			strReturn = strReturn + B0
			strComplement = strComplement + B1

		for i in range(3):
			strReturn = strReturn + B0
			strComplement = strComplement + B1

		strReturn = strReturn + strComplement
		strReturn = strReturn + STOP_CODE
		return {'S': strReturn}
