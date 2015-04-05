# -*- coding: utf-8 -*-

class Device(object):
	def __init__(self, type = None, location = None):
		self.type = type
		self.location = location

	@staticmethod
	def fromSSDPResponse(response):
		return Device(type=response.deviceType, location=response.location)
