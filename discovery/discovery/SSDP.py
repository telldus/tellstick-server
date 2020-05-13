# -*- coding: utf-8 -*-
import logging
from typing import Dict, Tuple
from xml.etree import ElementTree

import requests
import ssdp

_LOGGER = logging.getLogger(__name__)

SSDP_PORT = 1900


class SSDPDevice:
	def __init__(self, entry, st, usn):
		self._entry = entry
		self._st = st
		self._usn = usn

	@property
	def location(self) -> str:
		"""Return Location value."""
		return self._entry.location

	@property
	def st(self) -> str:  # pylint: disable=invalid-name
		"""Return ST value."""
		return self._st

	@property
	def usn(self) -> str:
		"""Return USN value."""
		return self._usn

	def __getattr__(self, key) -> str:
		return self._entry.getDeviceEntry(key)

	def __repr__(self):
		"""Return the entry."""
		return "<SSDPDevice {}>".format(self.st or '')


class SSDPEntry:
	def __init__(self, location):
		self._location = location
		self._tree = None
		self._devices: Dict[str, SSDPDevice] = {}

	def addDevice(self, device: SSDPDevice) -> bool:
		if device.st in self._devices:
			return False
		self._devices[device.st] = device
		return True

	def getDeviceEntry(self, key: str) -> str:
		if not self._tree:
			xml = requests.get(self.location, timeout=5).text
			self._tree = ElementTree.fromstring(xml)
		for device in self.getNode(self._tree, "device"):
			for node in self.getNode(device, key):
				return node.text
		return None

	@property
	def location(self) -> str:
		"""Return Location value."""
		return self._location

	def __repr__(self):
		"""Return the entry."""
		return "<SSDPEntry {}>".format(self.location or '')

	@staticmethod
	def getNode(node: ElementTree, tagName: str):
		for child in node:
			tag = child.tag[child.tag.find("}") + 1:]
			if tag == tagName:
				yield child


class SSDPListener(ssdp.SimpleServiceDiscoveryProtocol):
	def __init__(self, parent):
		self.parent = parent
		self.entries = {}
		self.transport = None

	def response_received(
	    self, response: ssdp.SSDPResponse, addr: Tuple[str, int]
	):
		location = response.location
		if location not in self.entries:
			entry = SSDPEntry(location)
			self.entries[location] = entry
		device = SSDPDevice(self.entries[location], response.st, response.usn)
		if self.entries[location].addDevice(device):
			self.parent.SSDPDeviceDiscovered(device)

	def request_received(self, request, addr):
		pass

	def connection_made(self, transport):
		self.transport = transport

	def scan(self):
		if not self.transport:
			return
		notify = ssdp.SSDPRequest(
		    'M-SEARCH',
		    headers={
		        'HOST': SSDPListener.MULTICAST_ADDRESS,
		        'MAN': "ssdp:discover",
		        "MX": 1,
		        "ST": "ssdp:all",
		    }
		)
		notify.sendto(self.transport, (SSDPListener.MULTICAST_ADDRESS, SSDP_PORT))
