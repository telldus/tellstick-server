# -*- coding: utf-8 -*-

import time, random
import threading

from base import Application, Settings, IInterface, ObserverCollection

#from configobj import ConfigObj

from ServerList import *
from ServerConnection import ServerConnection
#from TelldusCore import *
from LiveMessage import *

class ITelldusLiveObserver(IInterface):
	def liveRegistered():
		"""This method is called when we have succesfully registered with a Live! server"""
	def liveDisconnected():
		"""This method is call when we are disconnected"""

class TelldusLive(threading.Thread):
	_instance = None
	_initialized = False
	observers = ObserverCollection(ITelldusLiveObserver)

	def __new__(cls, *args, **kwargs):
		if not cls._instance:
			cls._instance = super(TelldusLive, cls).__new__(cls, *args, **kwargs)
		return cls._instance

	def __init__(self):
		if TelldusLive._initialized:
			return
		TelldusLive._initialized = True
		super(TelldusLive,self).__init__()
		self.context = Application().pluginContext
		print("Telldus Live! loading")
		self.supportedMethods = 0
		self.handlers = {}
		self.registered = False
		self.serverList = ServerList()
		Application().registerShutdown(self.stop)
		self.s = Settings('tellduslive.config')
		self.uuid = self.s['uuid']
		self.conn = ServerConnection()
		self.pingTimer = 0
		self.start()

	def handleMessage(self, message):
		if (message.name() == "notregistered"):
			params = message.argument(0).dictVal
			self.s['uuid'] = params['uuid'].stringVal
			print("This client isn't activated, please activate it using this url:\n%s" % params['url'].stringVal)
			return

		if (message.name() == "registered"):
			self.registered = True
			self.observers.liveRegistered()

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
			return

		if message.name() in self.handlers:
			for handler in self.handlers[message.name()]:
				handler(message)
			return
		print "Did not understand: %s" % message.toByteArray()

	def registerHandler(self, message, fn):
		if message not in self.handlers:
			self.handlers[message] = []
		self.handlers[message].append(fn)

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
				print("Disconnected, reconnect in %i seconds" % wait)
				self.observers.liveDisconnected()

			else:
				if (time.time() - pongTimer >= 360):  # No pong received
					self.conn.close()
					wait = random.randint(10, 50)
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

	def __sendRegisterMessage(self):
		print("Send register")
		uuid = self.s['uuid']
		msg = LiveMessage('Register')
		msg.append({
			'key': self.conn.publicKey,
			'uuid': uuid,
			'hash': 'sha1'
		})
		msg.append({
			'protocol': 2,
			'version': '1',
			'os': 'linux',
			'os-version': 'telldus'
		})
		self.conn.send(msg)
