# -*- coding: utf-8 -*-

import logging
from zeroconf import Zeroconf
from base import Application

_LOGGER = logging.getLogger(__name__)


class ZeroconfListener:
	def __init__(self, parent):
		self.parent = parent
		self.filters = []
		self.zeroconf = Zeroconf()

	def addFilter(self, serviceFilter, callback):
		service = serviceFilter.get('type', None)
		if not service:
			return
		self.filters.append((serviceFilter, callback))
		self.zeroconf.add_service_listener(service, self)

	def remove_service(self, zeroconf, serviceType, name):
		pass

	def add_service(self, zeroconf, serviceType, name):
		# New device was found on the network
		info = zeroconf.get_service_info(serviceType, name)
		for serviceFilter, callback in self.filters:
			if serviceType != serviceFilter['type']:
				continue
			match = True
			for prop, value in serviceFilter.get('properties', {}).items():
				if value.encode('utf-8') != info.properties.get(prop.encode('utf-8')):
					match = False
					break
			if match:
				Application().createTask(callback, info)
				break
