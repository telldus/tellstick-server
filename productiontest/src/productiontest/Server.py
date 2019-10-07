#!/usr/bin/env python

import fcntl
import logging
import socket
import socketserver
import struct
from threading import Thread

from base import Application, implements, Plugin, IInterface, ISignalObserver, slot
from board import Board
from tellduslive.base import LiveMessage, TelldusLive
from rf433 import RF433, RF433Msg, Protocol
try:
	from zwave.telldus import IZWObserver, TelldusZWave
except ImportError:
	class IZWObserver(IInterface):
		pass
	TelldusZWave = None

class AutoDiscoveryHandler(socketserver.BaseRequestHandler):
	def handle(self):
		sock = self.request[1]
		product = ''.join(x.capitalize() for x in Board.product().split('-'))
		live = TelldusLive(Application.defaultContext())
		msg = '%s:%s:%s:%s:%s' % (
			product,
			AutoDiscoveryHandler.getMacAddr(Board.networkInterface()),
			Board.secret(),
			Board.firmwareVersion(),
			live.uuid,
		)
		sock.sendto(msg.encode(), self.client_address)

	@staticmethod
	def getMacAddr(ifname):
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		info = fcntl.ioctl(sock.fileno(), 0x8927, struct.pack('256s', bytes(ifname[:15], 'utf-8')))
		return ''.join(['%02X' % char for char in info[18:24]])

class CommandHandler(socketserver.BaseRequestHandler):
	rf433 = None
	context = None

	def handle(self):
		data = self.request[0].strip()
		self.socket = self.request[1]
		if data == b"B:reglistener":
			server = Server(CommandHandler.context)  # pylint: disable=E1121
			server.reglistener(self.socket, self.client_address)

		msg = LiveMessage.fromByteArray(data)
		if msg.name() == 'send':
			self.handleSend(msg.argument(0).toNative())

	@staticmethod
	def handleSend(msg):
		protocol = Protocol.protocolInstance(msg['protocol'])
		if not protocol:
			logging.warning("Unknown protocol %s", msg['protocol'])
			return
		protocol.setModel(msg['model'])
		protocol.setParameters({'house': msg['house'], 'unit': msg['unit']+1})
		msg = protocol.stringForMethod(msg['method'], None)
		if msg is None:
			logging.error("Could not encode rf-data")
			return
		CommandHandler.rf433.dev.queue(RF433Msg('S', msg['S'], {}))

class Server(Plugin):
	implements(IZWObserver)
	implements(ISignalObserver)

	def __init__(self):
		self.listener = None
		self.clientAddress = None
		CommandHandler.rf433 = RF433(self.context)
		CommandHandler.context = self.context
		if TelldusZWave is not None:
			self.zwave = TelldusZWave(self.context)
		Application().registerShutdown(self.__stop)
		self.autoDiscovery = socketserver.UDPServer(('0.0.0.0', 30303), AutoDiscoveryHandler)
		self.commandSocket = socketserver.UDPServer(('0.0.0.0', 42314), CommandHandler)
		Thread(target=self.__autoDiscoveryStart).start()
		Thread(target=self.__commandSocketStart).start()

	def reglistener(self, sock, clientAddress):
		self.listener = sock
		self.clientAddress = clientAddress
		self.sendVersion()

	@slot('rf433RawData')
	def rf433RawData(self, data, *__args, **__kwargs):
		if 'data' in data:
			data['data'] = int(data['data'], 16)
		msg = LiveMessage("RawData")
		msg.append(data)
		try:
			# nettester does not understand base64-encoding
			self.listener.sendto(msg.toByteArray(False), self.clientAddress)
		except Exception as __error:
			# for example if listener isn't set
			pass

	def zwaveReady(self):
		self.sendVersion()

	def sendVersion(self):
		if self.zwave is None or not self.zwave.controller.version():
			return  # nothing or not finished yet
		if not self.listener:
			return  # No listener registered
		msg = LiveMessage("zwaveinfo")
		msg.append({
			'version': self.zwave.controller.version()
		})
		try:
			# nettester does not understand base64-encoding
			self.listener.sendto(msg.toByteArray(False), self.clientAddress)
		except Exception as __error:
			# for example if listener isn't set
			pass

	def __autoDiscoveryStart(self):
		self.autoDiscovery.serve_forever()

	def __commandSocketStart(self):
		self.commandSocket.serve_forever()

	def __stop(self):
		self.autoDiscovery.shutdown()
		self.commandSocket.shutdown()
