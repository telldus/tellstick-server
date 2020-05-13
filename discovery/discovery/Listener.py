# -*- coding: utf-8 -*-
import asyncio
import logging
import socket

from base import Application, Plugin, signal

from .SSDP import SSDPListener, SSDPEntry

_LOGGER = logging.getLogger(__name__)


class Listener(Plugin):
	def __init__(self):
		logging.getLogger('ssdp').setLevel('INFO')
		self.ssdpListener: SSDPListener = None
		self.transport = None
		Application().createTask(self.setupSSDP)
		Application().registerShutdown(self.shutdown)

	@signal
	def SSDPDeviceDiscovered(self, device: SSDPEntry):  #pylint: disable=invalid-name
		"""Signal sent when a device was discovered on the network"""

	async def setupSSDP(self):
		loop = asyncio.get_event_loop()
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

		self.ssdpListener = SSDPListener(self)

		self.transport, _protocol = await loop.create_datagram_endpoint(
		    lambda: self.ssdpListener, sock=sock
		)
		Application().registerScheduledTask(
		    self.ssdpListener.scan, seconds=60, runAtOnce=False
		)

	def shutdown(self):
		self.transport.close()
