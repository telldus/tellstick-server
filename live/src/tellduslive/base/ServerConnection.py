# -*- coding: utf-8 -*-

import errno
import logging
import select
import socket
import ssl
from base import Settings
from .LiveMessage import LiveMessage

class ServerConnection(object):
	CLOSED, CONNECTING, CONNECTED, READY, MSG_RECEIVED, DISCONNECTED = list(range(6))

	def __init__(self):
		self.publicKey = ''
		self.privateKey = ''
		self.state = ServerConnection.CLOSED
		self.msgs = []
		self.server = None
		self.socket = None
		settings = Settings('tellduslive.config')
		self.useSSL = settings.get('useSSL', True)

	def close(self):
		self.state = ServerConnection.CLOSED
		try:
			self.socket.shutdown(socket.SHUT_RDWR)
			self.socket.close()
		except Exception as __error:
			pass

	def connect(self, address, port):
		if not self.useSSL:
			port = port + 2
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
			try:
				newSocket = socket.create_connection(self.server)
				ctx = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
				ctx.load_default_certs(purpose=ssl.Purpose.CLIENT_AUTH)
				if self.useSSL:
					self.socket = ctx.wrap_socket(newSocket)
				else:
					self.socket = newSocket
				self.state = ServerConnection.CONNECTED
			except socket.error as socketException:
				(error, errorString) = socketException.args
				logging.error("%s %s", str(error), (errorString))
				self.state = ServerConnection.CLOSED
				return ServerConnection.DISCONNECTED
			except Exception as error:
				logging.error(str(error))
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
		try:
			fileno = self.socket.fileno()
			readlist, __writelist, __xlist = select.select([fileno], [], [], 5)
		except Exception as error:
			logging.exception(error)
			self.close()
			return self.state
		if fileno not in readlist:
			return self.state
		if self.useSSL:
			resp = self._readSSL()
		else:
			resp = self._read()

		if resp is None:
			return ServerConnection.READY
		if (resp == b''):
			logging.warning("Empty response, disconnected? %s", str(self.state))
			if self.state == ServerConnection.CLOSED:
				return ServerConnection.CLOSED
			self.close()
			return ServerConnection.DISCONNECTED

		envelope = LiveMessage.fromByteArray(resp)
		if (not envelope.verifySignature('sha1', self.privateKey)):
			logging.warning("Signature failed")
			return ServerConnection.READY
		self.msgs.insert(0, LiveMessage.fromByteArray(envelope.argument(0).byteVal))
		return ServerConnection.MSG_RECEIVED

	def send(self, msg):
		if self.state != ServerConnection.CONNECTED and self.state != ServerConnection.READY:
			return
		signedMessage = msg.toSignedMessage('sha1', self.privateKey)
		try:
			if self.useSSL:
				retry = True
				while retry:
					retry = False
					try:
						if len(signedMessage) % 16384 == 0:
							# the server can't really handle
							# messages evenly divided by 16384
							# (SSL max size is 16384, and there
							# is no sure way of knowing if more
							# data is coming or not), add some
							# padding
							signedMessage = signedMessage + b'='
						self.socket.write(signedMessage)
					except socket.error as error:
						if isinstance(error.args, tuple):
							if error[0] == socket.SSL_ERROR_WANT_WRITE:
								# more to write
								retry = True
								continue
			else:
				self.socket.send(signedMessage)
		except Exception as error:
			logging.error('ERROR, could not write to socket. Close and reconnect')
			logging.error(str(error))
			self.close()

	def _readSSL(self):
		hasMoreData = True
		resp = bytearray()
		buffSize = 1024
		while (hasMoreData):
			try:
				data = self.socket.recv(buffSize)
				if (len(data) < buffSize):
					hasMoreData = False
				resp = resp + data
			except ssl.SSLError as error:
				if error.args[0] == ssl.SSL_ERROR_WANT_READ:
					pass
				else:
					logging.error("SSLSocket error: %s", str(error))
					return None
			except socket.error as error:
				logging.error("Socket error: %s", str(error))
				return None
			except Exception as error:
				logging.error(str(error))
				return None
		return resp

	def _read(self):
		hasMoreData = True
		request = bytearray()
		buffSize = 1024
		while (hasMoreData):
			try:
				packet = self.socket.recv(buffSize)
				if (len(packet) < buffSize):
					hasMoreData = False
				request = request + packet
			except socket.error as socketException:
				(err, errstr) = socketException.args
				if (err == errno.EAGAIN):
					return None
				return b''  # is not alive
		return request
