# -*- coding: utf-8 -*-

import socket, ssl, errno, select, logging
from LiveMessage import LiveMessage

class ServerConnection(object):
	CLOSED, CONNECTING, CONNECTED, READY, MSG_RECEIVED, DISCONNECTED = range(6)

	def __init__(self):
		self.publicKey = ''
		self.privateKey = ''
		self.state = ServerConnection.CLOSED
		self.msgs = []
		self.server = None

	def close(self):
			self.state = ServerConnection.CLOSED
			try:
				self.socket.shutdown(socket.SHUT_RDWR)
				self.socket.close()
			except:
				pass

	def connect(self, address, port):
		self.server = (address, port)
		self.state = ServerConnection.CONNECTING
		logging.info("Connecting to %s:%i" % (address, port))
		return True

	def popMessage(self):
		if len(self.msgs) == 0:
			return None
		return self.msgs.pop()

	def process(self):
		if self.state == ServerConnection.CLOSED:
			return ServerConnection.CLOSED
		if self.state == ServerConnection.CONNECTING:
			self.socket = ssl.wrap_socket(
				socket.socket(socket.AF_INET, socket.SOCK_STREAM),
				ssl_version=ssl.PROTOCOL_TLSv1,
				ca_certs="/etc/ssl/certs/ca-certificates.crt",
				cert_reqs=ssl.CERT_REQUIRED
			)
			try:
				self.socket.connect(self.server)
				self.state = ServerConnection.CONNECTED
			except socket.error as (error, errorString):
				logging.error("%s %s", str(error), (errorString))
				self.state = ServerConnection.CLOSED
				return ServerConnection.DISCONNECTED
			except Exception as e:
				logging.error(str(e))
				self.state = ServerConnection.CLOSED
				return ServerConnection.DISCONNECTED
			logging.info("Connected to Telldus Live! server")
			self.state = ServerConnection.CONNECTED
			return self.state
		if self.state == ServerConnection.CONNECTED:
			self.socket.settimeout(0)
			self.state = ServerConnection.READY
			return ServerConnection.READY
		if len(self.msgs):
			return ServerConnection.MSG_RECEIVED

		fileno = self.socket.fileno()
		r, w, e = select.select([fileno], [], [], 5)
		if fileno not in r:
			return self.state
		try:
			resp = self.socket.recv(1024)
		except socket.error as e:
			# Timeout
			logging.error("Socket error!", str(e))
			return ServerConnection.READY
		except Exception as e:
			logging.error(str(e))
		dataLeft = self.socket.pending()
		while dataLeft:
			resp += self.socket.recv(dataLeft)
			dataLeft = self.socket.pending()

		if (resp == ''):
			logging.warning("Empty response, disconnected? %s", str(self.state))
			if self.state == ServerConnection.CLOSED:
				return ServerConnection.CLOSED
			self.close()
			return ServerConnection.DISCONNECTED

		envelope = LiveMessage.fromByteArray(resp)
		if (not envelope.verifySignature('sha1', self.privateKey)):
			logging.warning("Signature failed")
			return ServerConnection.READY
		self.msgs.insert(0, LiveMessage.fromByteArray(envelope.argument(0).stringVal))
		return ServerConnection.MSG_RECEIVED

	def send(self, msg):
		if self.state != ServerConnection.CONNECTED and self.state != ServerConnection.READY:
			return
		signedMessage = msg.toSignedMessage('sha1', self.privateKey)
		try:
			self.socket.write(signedMessage)
		except Exception as e:
			logging.error('ERROR, could not write to socket. Close and reconnect')
			logging.error(str(e))
			self.close()
