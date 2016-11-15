 # -*- coding: utf-8 -*-

from Protocol import Protocol
from telldus import Device

class ProtocolIkea(Protocol):
	def methods(self):
		if self.model == 'selflearning-switch':
			return (Device.TURNON | Device.TURNOFF)
		return (Device.TURNON | Device.TURNOFF | Device.DIM)

	def stringForMethod(self, method, level=None):
		intSystem = self.intParameter('system', 1, 16)-1
		intFadeStyle = 1 if self.stringParameter('fade', 'true') == 'true' else 0
		strUnits = self.stringParameter('units', '')

		if method == Device.TURNON:
			level = 255
		elif method == Device.TURNOFF:
			level = 0
		elif method == Device.DIM:
			pass
		else:
			return None

		if strUnits == '':
			return None

		intUnits = 0  # Start without any units

		for intUnit in strUnits.split(','):
			if intUnit == '10':
				intUnit = 0
			intUnits = intUnits | ( 1<<(9-int(intUnit)) )

		strReturn = 'TTTTTT' + chr(170)  # Startcode, always like this

		strChannels = ''
		intCode = (intSystem << 10) | intUnits
		checksum1 = 0
		checksum2 = 0
		for i in range(13, -1, -1):
			if (intCode>>i) & 1:
				strChannels += 'TT'
				if i % 2 == 0:
					checksum2 += 1
				else:
					checksum1 += 1
			else:
				strChannels += chr(170)
		strReturn += strChannels  # System + Units

		strReturn += 'TT' if checksum1 % 2 == 0 else chr(170)  # 1st checksum
		strReturn += 'TT' if checksum2 % 2 == 0 else chr(170)  # 2nd checksum

		intLevel = 0
		if level <= 12:
			intLevel = 10  #  Level 10 is actually off
		elif level <= 37:
			intLevel = 1
		elif level <= 62:
			intLevel = 2
		elif level <= 87:
			intLevel = 3
		elif level <= 112:
			intLevel = 4
		elif level <= 137:
			intLevel = 5
		elif level <= 162:
			intLevel = 6
		elif level <= 187:
			intLevel = 7
		elif level <= 212:
			intLevel = 8
		elif level <= 237:
			intLevel = 9
		else:
			intLevel = 0  # Level 0 is actually full on

		intFade = 0
		if intFadeStyle == 1:
			intFade = 11 << 4  # Smooth
		else:
			intFade = 1 << 4  # Instant

		intCode = intLevel | intFade  # Concat level and fade

		checksum1 = 0
		checksum2 = 0
		for i in range(6):
			if (intCode>>i) & 1:
				strReturn += 'TT'
				if i % 2 == 0:
					checksum1 += 1
				else:
					checksum2 += 1
			else:
				strReturn += chr(170)

		strReturn += 'TT' if checksum1 % 2 == 0 else chr(170)  # 1st checksum
		strReturn += 'TT' if checksum2 % 2 == 0 else chr(170)  # 2nd checksum

		return {'S': strReturn}
