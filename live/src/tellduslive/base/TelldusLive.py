# -*- coding: utf-8 -*-

import socket, ssl
import time, os
import threading

from base import Application, Settings

#from configobj import ConfigObj

from ServerList import *
#from TelldusCore import *
from LiveMessage import *

class TelldusLive(threading.Thread):
	_instance = None
	_initialized = False

	def __new__(cls, *args, **kwargs):
		if not cls._instance:
			cls._instance = super(TelldusLive, cls).__new__(cls, *args, **kwargs)
		return cls._instance

	def __init__(self):
		if TelldusLive._initialized:
			return
		TelldusLive._initialized = True
		super(TelldusLive,self).__init__()
		print("Telldus Live! loading")
		self.publicKey = ''
		self.privateKey = ''
		self.hashMethod = 'sha1'
		self.pongTimer = 0
		self.pingTimer = 0
		self.supportedMethods = 0
		self.handlers = {}
		self.serverList = ServerList()
		Application().registerShutdown(self.stop)
		self.s = Settings('tellduslive.config')
		self.uuid = self.s['uuid']
		self.start()

	def handleMessage(self, message):
		if (message.name() == "notregistered"):
			params = message.argument(0).dictVal
			self.s['uuid'] = params['uuid'].stringVal
			print("This client isn't activated, please activate it using this url:\n%s" % params['url'].stringVal)
			return

		#if (message.name() == "registered"):
			#params = message.argument(0).dictVal
			#self.supportedMethods = params['supportedMethods'].intVal
			#self.tellduscore.setSupportedMethods(self.supportedMethods)
			#self.sendDevicesReport()
			#return

		if (message.name() == "command"):
			# Extract ACK and handle it
			args = message.argument(0).dictVal
			if 'ACK' in args:
				msg = LiveMessage("ACK")
				msg.append(args['ACK'].intVal)
				self.send(msg)

		if (message.name() == "pong"):
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
		server = self.serverList.popServer()
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket = ssl.wrap_socket(s, ssl_version=ssl.PROTOCOL_TLSv1, ca_certs="/etc/ssl/certs/ca-certificates.crt",cert_reqs=ssl.CERT_REQUIRED)
		self.socket.settimeout(5)
		self.socket.connect((server['address'], int(server['port'])))

		uuid = self.s['uuid']
		msg = LiveMessage('Register')
		msg.append({
			'key': self.publicKey,
			'uuid': uuid,
			'hash': self.hashMethod
		})
		msg.append({
			'protocol': 2,
			'version': '1',
			'os': 'linux',
			'os-version': 'telldus'
		})

		self.socket.write(self.signedMessage(msg))
		self.pongTimer = time.time()
		self.pingTimer = time.time()
		while(self.running):
			try:
				resp = self.socket.read(1024)
			except ssl.SSLError:
				# Timeout, try again after some maintenance
				if (time.time() - self.pongTimer >= 360):  # No pong received
					print("No pong received, disconnecting")
					break
				if (time.time() - self.pingTimer >= 120):
					# Time to ping
					msg = LiveMessage("Ping")
					self.socket.write(self.signedMessage(msg))
					self.pingTimer = time.time()

				continue

			if (resp == ''):
				print("no response")
				break

			envelope = LiveMessage.fromByteArray(resp)
			if (not envelope.verifySignature(self.hashMethod, self.privateKey)):
				print("Signature failed")
				continue

			self.pongTimer = time.time()
			#print("Handle message", envelope.argument(0).stringVal)
			app.queue(self.handleMessage, LiveMessage.fromByteArray(envelope.argument(0).stringVal))

	def stop(self):
		self.running = False

	def send(self, message):
		self.socket.write(self.signedMessage(message))

	def signedMessage(self, message):
		return message.toSignedMessage(self.hashMethod, self.privateKey)

'''	def connect(self, server):

		try:
			uuid = self.config['uuid']
		except:
			pass

	def handleCommand(self, args):
		if (args['action'].stringVal == 'turnon'):
			self.tellduscore.turnon(args['id'].intVal)
		elif (args['action'].stringVal == 'turnoff'):
			self.tellduscore.turnoff(args['id'].intVal)
		else:
			return

		if ('ACK' in args):
			#Respond to ack
			msg = LiveMessage("ACK")
			msg.append(args['ACK'].intVal)
			self.socket.write(self.signedMessage(msg))

	


	def sendDevicesReport(self):
		msg = LiveMessage("DevicesReport")
		msg.append(self.tellduscore.getList())
		self.socket.write(self.signedMessage(msg))
'''
