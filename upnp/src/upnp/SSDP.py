# -*- coding: utf-8 -*-

import socket
import httplib
import StringIO
from Device import Device
from threading import Thread
from base import ObserverCollection, IInterface, Plugin, mainthread

class ISSDPNotifier(IInterface):
	def ssdpRootDeviceFound(rootDevice):
		"""This method is called when a root device is found on the network"""
	def ssdpDeviceFound(device):
		"""This method is called when a device is found on the network"""
	def ssdpServiceFound(service):
		"""This method is called when a service is found on the network"""

class SSDPResponse(object):
	ST_ROOT_DEVICE, ST_DEVICE, ST_SERVICE, ST_UNKNOWN = range(4)

	class _FakeSocket(StringIO.StringIO):
		def makefile(self, *args, **kw):
			return self
	def __init__(self, response):
		r = httplib.HTTPResponse(self._FakeSocket(response))
		r.begin()
		self.location = r.getheader("location")
		self.usn = r.getheader("usn")
		self.st = r.getheader("st")
		self.cache = r.getheader("cache-control").split("=")[1]
		index = self.usn.find('::')
		if index >= 0:
			self.uuid = self.usn[5:index]
		else:
			self.uuid = self.usn[5:]
		self.type = SSDPResponse.ST_UNKNOWN
		if self.st == 'upnp:rootdevice':
			self.type = SSDPResponse.ST_ROOT_DEVICE
		elif self.st.startswith('urn:schemas-upnp-org:device'):
			self.type = SSDPResponse.ST_DEVICE
			self.deviceType = self.st[28:]

class SSDP(Plugin):
	observers = ObserverCollection(ISSDPNotifier)

	def __init__(self):
		self.rootDevices = {}
		self.devices = {}
		Thread(target=self.discover).start()

	def discover(self):
		service = "ssdp:all"
		group = ("239.255.255.250", 1900)
		message = "\r\n".join([
			'M-SEARCH * HTTP/1.1',
			'HOST: {0}:{1}',
			'MAN: "ssdp:discover"',
			'ST: {st}','MX: 3','',''])
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
		sock.settimeout(5)
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
		sock.sendto(message.format(*group, st=service), group)
		while True:
			try:
				response = SSDPResponse(sock.recv(1024))
				if response.type == SSDPResponse.ST_ROOT_DEVICE:
					pass
				elif response.type == SSDPResponse.ST_DEVICE:
					device = Device.fromSSDPResponse(response)
					self.devices[response.uuid] = device
			except socket.timeout:
				break
		self.__discoveryDone()

	@mainthread
	def __discoveryDone(self):
		for i in self.devices:
			self.observers.ssdpDeviceFound(self.devices[i])
