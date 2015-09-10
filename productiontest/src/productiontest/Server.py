#!/usr/bin/env python

from base import Application, Plugin
from board import Board
from tellduslive.base import LiveMessage
from rf433 import RF433, RF433Msg, Protocol
from threading import Thread
from zwave.telldus import TelldusZWave
import SocketServer
import socket, fcntl, struct
import logging

class AutoDiscoveryHandler(SocketServer.BaseRequestHandler):
	def handle(self):
		data = self.request[0].strip()
		socket = self.request[1]
		product = ''.join(x.capitalize() for x in Board.product().split('-'))
		msg = '%s:%s:%s:%s' % (product, AutoDiscoveryHandler.getMacAddr(Board.networkInterface()), Board.secret(), Board.firmwareVersion())
		socket.sendto(msg, self.client_address)

	@staticmethod
	def getMacAddr(ifname):
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		info = fcntl.ioctl(s.fileno(), 0x8927,  struct.pack('256s', ifname[:15]))
		return ''.join(['%02X' % ord(char) for char in info[18:24]])

class CommandHandler(SocketServer.BaseRequestHandler):
	rf433 = None
	zwave = None

	def handle(self):
		data = self.request[0].strip()
		socket = self.request[1]
		if data == "B:reglistener":
			msg = LiveMessage("zwaveinfo")
			msg.append({
				'version': CommandHandler.zwave.controller.version()
			})
			socket.sendto(msg.toByteArray(), self.client_address)


		msg = LiveMessage.fromByteArray(data)
		if msg.name() == 'send':
			self.handleSend(msg.argument(0).toNative())

	def handleSend(self, msg):
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
	def __init__(self):
		CommandHandler.rf433 = RF433(self.context)
		CommandHandler.zwave = TelldusZWave(self.context)
		Application().registerShutdown(self.__stop)
		self.autoDiscovery = SocketServer.UDPServer(('0.0.0.0', 30303), AutoDiscoveryHandler)
		self.commandSocket = SocketServer.UDPServer(('0.0.0.0', 42314), CommandHandler)
		Thread(target=self.__autoDiscoveryStart).start()
		Thread(target=self.__commandSocketStart).start()

	def __autoDiscoveryStart(self):
		self.autoDiscovery.serve_forever()

	def __commandSocketStart(self):
		self.commandSocket.serve_forever()

	def __stop(self):
		self.autoDiscovery.shutdown()
		self.commandSocket.shutdown()
