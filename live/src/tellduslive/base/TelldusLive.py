# -*- coding: utf-8 -*-

import time, random
import threading

from base import Application, Settings, IInterface, ObserverCollection, Plugin

#from configobj import ConfigObj

from ServerList import *
from ServerConnection import ServerConnection
#from TelldusCore import *
from LiveMessage import *

class ITelldusLiveObserver(IInterface):
	def liveRegistered(params):
		"""This method is called when we have succesfully registered with a Live! server"""
	def liveDisconnected():
		"""This method is call when we are disconnected"""

class TelldusLive(Plugin):
	observers = ObserverCollection(ITelldusLiveObserver)

	def __init__(self):
		print("Telldus Live! loading")
		self.supportedMethods = 0
		self.registered = False
		self.serverList = ServerList()
		Application().registerShutdown(self.stop)
		self.s = Settings('tellduslive.config')
		self.uuid = self.s['uuid']
		self.conn = ServerConnection()
		self.pingTimer = 0
		self.thread = threading.Thread(target=self.run)
		self.thread.start()

	def handleMessage(self, message):
		if (message.name() == "notregistered"):
			params = message.argument(0).dictVal
			self.s['uuid'] = params['uuid'].stringVal
			print("This client isn't activated, please activate it using this url:\n%s" % params['url'].stringVal)
			return

		if (message.name() == "registered"):
			self.registered = True
			self.observers.liveRegistered(message.argument(0).toNative())
			return

		if (message.name() == "command"):
			# Extract ACK and handle it
			args = message.argument(0).dictVal
			if 'ACK' in args:
				msg = LiveMessage("ACK")
				msg.append(args['ACK'].intVal)
				self.send(msg)

		if (message.name() == "pong"):
			return

		if (message.name() == "disconnect"):
			self.conn.close()
			self.registered = False
			return

		handled = False
		for o in self.observers:
			for f in getattr(o, '_telldusLiveHandlers', {}).get(message.name(), []):
				f(o, message)
				handled = True
		if not handled:
			print "Did not understand: %s" % message.toByteArray()


	def isRegistered(self):
		return self.registered

	def run(self):
		self.running = True
		app = Application()

		wait = 0
		pongTimer, self.pingTimer = (0, 0)
		while self.running:
			if wait > 0:
				wait = wait - 1
				time.sleep(1)
				continue
			state = self.conn.process()
			if state == ServerConnection.CLOSED:
				server = self.serverList.popServer()
				if not server:
					wait = random.randint(60, 300)
					print("No servers found, retry in %i seconds" % wait)
					continue
				if not self.conn.connect(server['address'], int(server['port'])):
					wait = random.randint(60, 300)
					print("Could not connect, retry in %i seconds" % wait)

			elif state == ServerConnection.CONNECTED:
				pongTimer, self.pingTimer = (time.time(), time.time())
				self.__sendRegisterMessage()

			elif state == ServerConnection.MSG_RECEIVED:
				msg = self.conn.popMessage()
				if msg is None:
					continue
				pongTimer = time.time()
				app.queue(self.handleMessage, msg)

			elif state == ServerConnection.DISCONNECTED:
				wait = random.randint(10, 50)
				self.registered = False
				print("Disconnected, reconnect in %i seconds" % wait)
				self.observers.liveDisconnected()

			else:
				if (time.time() - pongTimer >= 360):  # No pong received
					self.conn.close()
					wait = random.randint(10, 50)
					self.registered = False
					print("No pong received, disconnecting. Reconnect in %i seconds" % wait)
					self.observers.liveDisconnected()
				elif (time.time() - self.pingTimer >= 120):
					# Time to ping
					self.conn.send(LiveMessage("Ping"))
					self.pingTimer = time.time()

	def stop(self):
		self.running = False

	def send(self, message):
		self.conn.send(message)
		self.pingTimer = time.time()

	def pushToWeb(self, module, action, data):
		msg = LiveMessage("sendToWeb")
		msg.append(module)
		msg.append(action)
		msg.append(data)
		self.send(msg)

	@staticmethod
	def handler(message):
		def call(fn):
			import sys
			frame = sys._getframe(1)
			frame.f_locals.setdefault('_telldusLiveHandlers', {}).setdefault(message, []).append(fn)
			return fn
		return call

	def __firmwareVersion(self):
		with open('/etc/builddate') as f:
			return f.readline().strip()

	def __sendRegisterMessage(self):
		print("Send register")
		msg = LiveMessage('Register')
		msg.append({
			'key': self.conn.publicKey,
			'mac': TelldusLive.getMacAddr('eth0'),
			'secret': TelldusLive.getSecret(),
			'hash': 'sha1'
		})
		msg.append({
			'protocol': 2,
			'version': self.__firmwareVersion(),
			'os': 'linux',
			'os-version': 'telldus'
		})
		self.conn.send(msg)

	@staticmethod
	def getMacAddr(ifname):
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		info = fcntl.ioctl(s.fileno(), 0x8927,  struct.pack('256s', ifname[:15]))
		return ''.join(['%02X' % ord(char) for char in info[18:24]])

	@staticmethod
	def getSecret():
		with open('/etc/board/uEnv.txt') as f:
			for line in f.readlines():
				args = line.strip().split('=')
				if len(args) < 2:
					continue
				if args[0] == 'secret':
					return args[1]
		return ''
