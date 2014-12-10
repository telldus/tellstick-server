# -*- coding: utf-8 -*-

import logging
from telldus import Device

class ProtocolOregon():
	def __init__(self):
		pass

	def decodeData(self, data):
		if 'data' not in data or 'model' not in data:
			return None
		msg = None
		value = int(data['data'], 16)
		model = int(data['model'], 16)

		if model == 0xEA4C:
			msg = self.decodeEA4C(value)
		elif model == 0x1A2D:
			msg = self.decode1A2D(value)
		elif model == 0xF824:
			# protocol version 3, e.g. THGR810
			msg = self.decodeF824(value)
		elif model == 0x1984 or model == 0x1994:
			# protocol version 3, wind
			msg = self.decode1984(value, model)
		elif model == 0x2914:
			# protocol version 3, rain
			msg = self.decode2914(value)
		elif model == 0xC844 or model == 0xEC40:
			# protocol version 3, pool thermometer, EC40 not yet tested
			msg = self.decodeC844(value, model)
		elif model == 0xD874:
			# protocol version 3, UV index
			msg = self.decodeD874(value)

		if not msg:
			return None

		data['model'] = '%X' % model

		for key in msg:
			data[key] = msg[key]
		return data

	def decodeEA4C(self, value):
		checksum = 0xE + 0xA + 0x4 + 0xC
		checksum -= (value & 0xF) * 0x10
		checksum -= 0xA
		value >>= 8

		checksumw = (value >> 4) & 0xF
		neg = value & (1 << 3)
		hundred = value & 3
		checksum += (value & 0xF)
		value >>= 8

		temp2 = value & 0xF
		temp1 = (value >> 4) & 0xF
		checksum += temp2 + temp1
		value >>= 8

		temp3 = (value >> 4) & 0xF
		checksum += (value & 0xF) + temp3
		value >>= 8

		checksum += ((value >> 4) & 0xF) + (value & 0xF)
		address = value & 0xFF
		value >>= 8

		checksum += ((value >> 4) & 0xF) + (value & 0xF)
		channel = (value >> 4) & 0x7

		if checksum != checksumw:
			return None

		temp = int('%d%d' % (temp2, temp3))/10.0
		temp = temp + (10*int(temp1)) + (100*hundred)
		if neg:
			temp = 0 - temp

		valueList = []
		valueList.append({'type': Device.TEMPERATURE, 'value': temp, 'scale': Device.SCALE_TEMPERATURE_CELCIUS})
		return {'id': int(address), 'values': valueList}

	def decode1984(self, value, model):
		# wind
		crcCheck = value & 0xF # Perhaps CRC?
		value >>= 4
		messageChecksum1 = value & 0xF
		value >>= 4
		messageChecksum2 = value & 0xF

		value >>= 4
		avg1 = value & 0xF
		value >>= 4
		avg2 = value & 0xF
		value >>= 4
		avg3 = value & 0xF

		value >>= 4
		gust1 = value & 0xF
		value >>= 4
		gust2 = value & 0xF
		value >>= 4
		gust3 = value & 0xF

		value >>= 4
		unknown1 = value & 0xF
		value >>= 4
		unknown2 = value & 0xF

		value >>= 4
		direction = value & 0xF
		directiondegrees = direction * 22.5

		value >>= 4
		battery = value & 0xF #PROBABLY battery

		value >>= 4
		rollingcode = ((value >> 4) & 0xF) + (value & 0xF)
		checksum = ((value >> 4) & 0xF) + (value & 0xF)
		value >>= 8
		channel = value & 0xF

		checksum += unknown1 + unknown2 + avg1 + avg2 + avg3 + gust1 + gust2 + gust3 + direction + battery + channel
		if model == 0x1984:
			checksum += 0x1 + 0x9 + 0x8 + 0x4
		elif model == 0x1994:
			checksum += 0x1 + 0x9 + 0x9 + 0x4

		if not ((checksum >> 4) & 0xF == messageChecksum1 and (checksum & 0xF) == messageChecksum2):
			#checksum error
			return None

		avg = (avg1*10) + avg2 + (avg3/10.0)

		gust = (gust1*10) + gust2 + (gust3/10.0)

		valueList = []
		valueList.append({'type': Device.WINDDIRECTION, 'value': directiondegrees, 'scale': Device.SCALE_WIND_DIRECTION})
		valueList.append({'type': Device.WINDAVERAGE, 'value': avg, 'scale': Device.SCALE_WIND_VELOCITY_MS})
		valueList.append({'type': Device.WINDGUST, 'value': gust, 'scale': Device.SCALE_WIND_VELOCITY_MS})

		return {'id': int(rollingcode), 'values': valueList, 'battery': battery}


	def decode1A2D(self, value):
		checksum2 = value & 0xFF
		value >>= 8
		checksum1 = value & 0xFF
		value >>= 8

		checksum = ((value >> 4) & 0xF) + (value & 0xF)
		hum1 = value & 0xF
		value >>= 8

		checksum += ((value >> 4) & 0xF) + (value & 0xF)
		neg = value & (1 << 3)
		hum2 = (value >> 4) & 0xF
		value >>= 8

		checksum += ((value >> 4) & 0xF) + (value & 0xF)
		temp2 = value & 0xF
		temp1 = (value >> 4) & 0xF
		value >>= 8

		checksum += ((value >> 4) & 0xF) + (value & 0xF)
		temp3 = (value >> 4) & 0xF
		value >>= 8

		checksum += ((value >> 4) & 0xF) + (value & 0xF)
		address = value & 0xFF
		value >>= 8

		checksum += ((value >> 4) & 0xF) + (value & 0xF)
		channel = (value >> 4) & 0x7

		checksum += 0x1 + 0xA + 0x2 + 0xD - 0xA

		#TODO: Find out how checksum2 works
		if checksum != checksum1:
			return None

		temp = (temp1*10) + temp2 + (temp3/10.0)
		if neg:
			temp = -temp

		valueList = []
		valueList.append({'type': Device.TEMPERATURE, 'value': temp, 'scale': Device.SCALE_TEMPERATURE_CELCIUS})
		valueList.append({'type': Device.HUMIDITY, 'value': int('%d%d' % (hum1, hum2)), 'scale': Device.SCALE_HUMIDITY_PERCENT})
		return {'id': int(address), 'values': valueList}

	def decode2914(self, value):
		# rain
		inchToCm = 25.4

		messageChecksum1 = value & 0xF
		value >>= 4
		messageChecksum2 = value & 0xF

		value >>= 4
		totRain1 = value & 0xF
		value >>= 4
		totRain2 = value & 0xF
		value >>= 4
		totRain3 = value & 0xF
		value >>= 4
		totRain4 = value & 0xF
		value >>= 4
		totRain5 = value & 0xF
		value >>= 4
		totRain6 = value & 0xF

		value >>= 4
		rainRate1 = value & 0xF
		value >>= 4
		rainRate2 = value & 0xF
		value >>= 4
		rainRate3 = value & 0xF
		value >>= 4
		rainRate4 = value & 0xF

		value >>= 4
		battery = value & 0xF #PROBABLY battery

		value >>= 4
		rollingcode = ((value >> 4) & 0xF) + (value & 0xF)
		checksum = ((value >> 4) & 0xF) + (value & 0xF)
		value >>= 8
		channel = value & 0xF

		checksum += totRain1 + totRain2 + totRain3 + totRain4 + totRain5 + totRain6 + rainRate1 + rainRate2 + rainRate3 + rainRate4 + battery + channel + 0x2 + 0x9 + 0x1 + 0x4

		if not ((checksum >> 4) & 0xF == messageChecksum1 and (checksum & 0xF) == messageChecksum2):
			#checksum error
			return None

		totRain = '%d.%d%d%d' % (totRain3, totRain4, totRain5, totRain6)
		if int(totRain2) > 0 or int(totRain1) > 0:
			totRain = '%d%s' % (totRain2, totRain)
			if int(totRain1) > 0:
				totRain = '%d%s' % (totRain1, totRain)
		totRain = round(float(totRain) * inchToCm, 1)

		rainRate = '%d.%d%d' % (rainRate2, rainRate3, rainRate4)
		if int(rainRate1) > 0:
			rainRate = '%d%s' % (rainRate1, rainRate)
		rainRate = round(float(rainRate) * inchToCm, 1)

		valueList = []
		valueList.append({'type': Device.RAINRATE, 'value': rainRate, 'scale': Device.SCALE_RAINRATE_MMH})
		valueList.append({'type': Device.RAINTOTAL, 'value': totRain, 'scale': Device.SCALE_RAINTOTAL_MM})
		return {'id': int(rollingcode), 'values': valueList, 'battery': battery}


	def decodeF824(self, value):
		crcCheck = value & 0xF #PROBABLY CRC
		value >>= 4
		messageChecksum1 = value & 0xF
		value >>= 4
		messageChecksum2 = value & 0xF

		value >>= 4
		unknown = value & 0xF
		value >>= 4
		hum1 = value & 0xF
		value >>= 4

		hum2 = value & 0xF
		value >>= 4
		neg = value & 0xF
		value >>= 4
		temp1 = value & 0xF
		value >>= 4
		temp2 = value & 0xF
		value >>= 4
		temp3 = value & 0xF
		value >>= 4
		battery = value & 0xF #PROBABLY battery

		value >>= 4
		rollingcode = ((value >> 4) & 0xF) + (value & 0xF)
		checksum = ((value >> 4) & 0xF) + (value & 0xF)
		value >>= 8
		channel = value & 0xF

		checksum += unknown + hum1 + hum2 + neg + temp1 + temp2 + temp3 + battery + channel + 0xF + 0x8 + 0x2 + 0x4

		if not ((checksum >> 4) & 0xF == messageChecksum1 and (checksum & 0xF) == messageChecksum2):
			#checksum error
			return None

		temp = (temp1*10) + temp2 + (temp3/10.0)
		if neg:
			temp = -temp

		valueList = []
		valueList.append({'type': Device.TEMPERATURE, 'value': temp, 'scale': Device.SCALE_TEMPERATURE_CELCIUS})
		valueList.append({'type': Device.HUMIDITY, 'value': int('%d%d' % (hum1, hum2)), 'scale': Device.SCALE_HUMIDITY_PERCENT})
		return {'id': int(rollingcode), 'values': valueList}

	def decodeC844(self, value, model):
		messageChecksum1 = value & 0xF
		value >>= 4
		messageChecksum2 = value & 0xF

		value >>= 4
		neg = value & 0xF
		value >>= 4
		temp1 = value & 0xF
		value >>= 4
		temp2 = value & 0xF
		value >>= 4
		temp3 = value & 0xF
		value >>= 4
		battery = value & 0xF #PROBABLY battery

		value >>= 4
		rollingcode = ((value >> 4) & 0xF) + (value & 0xF)
		checksum = ((value >> 4) & 0xF) + (value & 0xF)
		value >>= 8
		channel = value & 0xF

		checksum += neg + temp1 + temp2 + temp3 + battery + channel

		if model == 0xC844:
			checksum += 0xC + 0x8 + 0x4 + 0x4
		elif model == 0xEC40:
			checksum += 0xE + 0xC + 0x4 + 0x0

		if not ((checksum >> 4) & 0xF == messageChecksum1 and (checksum & 0xF) == messageChecksum2):
			#checksum error
			return None

		temp = (temp1*10) + temp2 + (temp3/10.0)
		if neg:
			temp = -temp

		valueList = []
		valueList.append({'type': Device.TEMPERATURE, 'value': temp, 'scale': Device.SCALE_TEMPERATURE_CELCIUS})
		return {'id': int(rollingcode), 'values': valueList}

	def decodeD874(self, value):
		messageChecksum1 = value & 0xF
		value >>= 4
		messageChecksum2 = value & 0xF

		value >>= 4
		unknown1 = value & 0xF
		value >>= 4
		unknown2 = value & 0xF
		value >>= 4
		uv1 = value & 0xF
		value >>= 4
		uv2 = value & 0xF
		value >>= 4
		battery = value & 0xF #PROBABLY battery

		value >>= 4
		rollingcode = ((value >> 4) & 0xF) + (value & 0xF)
		checksum = ((value >> 4) & 0xF) + (value & 0xF)
		value >>= 8
		channel = value & 0xF

		checksum += unknown1 + unknown2 + uv1 + uv2 + battery + channel + 0xD + 0x8 + 0x7 + 0x4

		if not ((checksum >> 4) & 0xF == messageChecksum1 and (checksum & 0xF) == messageChecksum2):
			#checksum error
			pass #TODO make checksums work

		if not (checksum & 0xF == messageChecksum1):
			#TODO temporary partial checksum check that seems to work
			return None

		uvindex = int('%d%d' % (uv1, uv2)) #TODO correct?

		valueList = []
		valueList.append({'type': Device.UV, 'value': uvindex, 'scale': Device.SCALE_UV_INDEX})
		return {'id': int(rollingcode), 'values': valueList, 'battery': battery}
