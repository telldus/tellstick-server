# -*- coding: utf-8 -*-

from base import Application
import fcntl, os, select, serial, threading, time
from .RF433Msg import RF433Msg
import logging
try:
	from pkg_resources import resource_filename
except ImportError:
	# pkg_resources not available, load firmware from filesystem
	def resource_filename(module, filename):
		raise Exception("Loading of firmware not implemented yet")

class Adapter(threading.Thread):
	BOOTLOADER_START = 0x7A00
	WAIT = b'w'
	INCOMING_START = '+'
	INCOMING_ALMOST_LAST = '\r'
	INCOMING_LAST = '\n'
	EMPTY_BUFFER = ''

	def __init__(self, handler, dev):
		super(Adapter,self).__init__()
		self.handler = handler
		self.devUrl = dev
		self.dev = None
		self.__queue = []
		self.__waitForResponse = None
		self.waitingForData = False
		Application().registerShutdown(self.__stop)
		(self.readPipe, self.writePipe) = os.pipe()
		fl = fcntl.fcntl(self.readPipe, fcntl.F_GETFL)
		fcntl.fcntl(self.readPipe, fcntl.F_SETFL, fl | os.O_NONBLOCK)
		self.start()

	def queue(self, msg):
		self.__queue.append(msg)
		if self.waitingForData:
			# Abort current read
			os.write(self.writePipe, Adapter.WAIT)

	def run(self):
		self.running = True
		app = Application()
		buffer = Adapter.EMPTY_BUFFER
		ttl = None
		state = 0

		while self.running:
			if self.dev is None:
				time.sleep(1)
				try:
					self.dev = serial.serial_for_url(self.devUrl, 115200, timeout=0)
				except Exception as e:
					self.dev = None
				continue

			if state == 0:
				x = self.__readByte(interruptable=True)
				if x == Adapter.EMPTY_BUFFER:
					if self.__waitForResponse is not None and self.__waitForResponse.queued + 5 < time.time():
						self.__waitForResponse.timeout()
						self.__waitForResponse = None
					if len(self.__queue) and self.__waitForResponse is None:
						state = 1
					continue
				if x == Adapter.INCOMING_ALMOST_LAST:
					continue
				if x == Adapter.INCOMING_START:
					# Start of data
					buffer = Adapter.EMPTY_BUFFER
					continue
				if x == Adapter.INCOMING_LAST:
					(cmd, params) = RF433Msg.parseResponse(buffer)
					if cmd is None:
						continue
					if self.__waitForResponse is not None:
						if cmd == self.__waitForResponse.cmd():
							self.__waitForResponse.response(params)
							self.__waitForResponse = None
							continue
					app.queue(self.handler.decodeData, cmd, params)
					continue
				buffer = buffer + x

			elif state == 1:
				if len(self.__queue) == 0:
					state = 0
					continue
				self.__waitForResponse = self.__queue.pop(0)
				self.__send(self.__waitForResponse.commandBytes())
				self.__waitForResponse.queued = time.time()
				state = 0

	def __stop(self):
		self.running = False
		if self.waitingForData:
			# Abort current read
			os.write(self.writePipe, Adapter.WAIT)

	def __readByte(self, interruptable = False):
		try:
			if interruptable:
				self.waitingForData = True
				i = [self.dev.fileno(), self.readPipe]
			else:
				i = [self.dev.fileno()]
			r, w, e = select.select(i, [], [], 1)
			if self.dev.fileno() in r:
				try:
					return self.dev.read().decode()
				except serial.SerialException as e:
					self.dev.close()
					self.dev = None
					logging.warning('Serial port lost')
					logging.exception(e)
					return Adapter.EMPTY_BUFFER
			if self.readPipe in r:
				try:
					while True:
						t = os.read(self.readPipe, 1)
				except Exception as e:
					pass
			return Adapter.EMPTY_BUFFER
		finally:
			self.waitingForData = False

	def __send(self, msg):
		self.dev.write(msg)
