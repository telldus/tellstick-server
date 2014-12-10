# -*- coding: utf-8 -*-

import logging
from telldus import Device

class ProtocolMandolyn():
	def __init__(self):
		pass

	def decodeData(self, data):
		if 'data' not in data:
			return None
		value = int(data['data'], 16)

		parity = value & 0x1
		value >>= 1

		temp = (value & 0x7FFF) - 6400
		temp = round(temp/128.0,1)
		value >>= 15

		humidity = (value & 0x7F)
		value >>= 7

		battOk = value & 0x1
		value >>= 3

		channel = (value & 0x3)+1
		value >>= 2

		house = value & 0xF

		data['id'] = int(house*10+channel)
		valueList = []
		valueList.append({'type': Device.TEMPERATURE, 'value': temp, 'scale': Device.SCALE_TEMPERATURE_CELCIUS})
		valueList.append({'type': Device.HUMIDITY, 'value': humidity, 'scale': Device.SCALE_HUMIDITY_PERCENT})
		data['values'] = valueList
		return data
