# -*- coding: utf-8 -*-

from telldus import Device
import crcmod.predefined
import struct
import logging

class ProtocolFineoffset():
	def __init__(self):
		pass

	def calculateChecksum(self, data):
		crc_8_func = crcmod.mkCrcFun(0x131, rev=False, initCrc=0x00)
		data = struct.pack('>I', data)
		return crc_8_func(data)

	def decodeData(self, data):
		if 'data' not in data:
			return None
		value = int(data['data'], 16)

		checksum = value & 0xFF
		value >>= 8

		if checksum != self.calculateChecksum(value):
			logging.warning("Wrong checksum for fineoffset, %i" % value)
			return None

		humidity = value & 0xFF
		value >>= 8

		temperature = (value & 0x7FF)/10.0
		value >>= 11

		if value & 0x1: #Negative
			temperature = -temperature
		value >>= 1

		id = value & 0xFF

		data['id'] = int(id)
		valueList = []
		valueList.append({'type': Device.TEMPERATURE, 'value': temperature, 'scale': Device.SCALE_TEMPERATURE_CELCIUS})
		if humidity <= 100:
			valueList.append({'type': Device.HUMIDITY, 'value': humidity, 'scale': Device.SCALE_HUMIDITY_PERCENT})
			data['model'] = 'temperaturehumidity'
		elif humidity == 0xFF:
			data['model'] = 'temperature'
		else:
			return None
		data['values'] = valueList

		return data
