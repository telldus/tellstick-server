# -*- coding: utf-8 -*-

from base import Application
import fcntl, os, select, serial, threading
import logging

class Adapter(threading.Thread):
	def __init__(self, handler, dev):
		super(Adapter,self).__init__()
		self.handler = handler
		self.setupHardware()
		self.waitingForData = False
		self.dev = serial.Serial(dev, 9600, timeout=0)
		Application().registerShutdown(self.stop)
		(self.readPipe, self.writePipe) = os.pipe()
		fl = fcntl.fcntl(self.readPipe, fcntl.F_GETFL)
		fcntl.fcntl(self.readPipe, fcntl.F_SETFL, fl | os.O_NONBLOCK)
		self.start()

	def run(self):
		self.running = True
		app = Application()
		buffer = ''

		while self.running:
			x = self.__readByte(interruptable=True)
			if x == '' or x == '\r':
				continue
			if x == '+':
				# Start of data
				buffer = ''
				continue
			if x == '\n':
				app.queue(self.handler.decodeData, buffer)
				continue
			buffer = buffer + x

	def setupHardware(self):
		# Make sure MCLR reset is pulled high (by setting the GPIO low)
		if os.path.exists('/sys/class/gpio/gpio5') == False:
			if os.path.exists('/sys/class/gpio/export') == False:
				logging.info("This doesn't look like an embedded board")
				return
			# Export the gpio
			with open('/sys/class/gpio/export', 'w') as f:
				f.write('5')
		if os.path.exists('/sys/class/gpio/gpio5') == False:
			print('Gpio not available even though it is exported. Something is wrong!')
			return
		with open('/sys/class/gpio/gpio5/direction', 'w') as f:
			f.write('out')
		with open('/sys/class/gpio/gpio5/value', 'w') as f:
			f.write('0')

	def stop(self):
		self.running = False
		if self.waitingForData:
			# Abort current read
			os.write(self.writePipe, 'w')

	def __readByte(self, interruptable = False):
		try:
			if interruptable:
				self.waitingForData = True
				i = [self.dev.fileno(), self.readPipe]
			else:
				i = [self.dev.fileno()]
			r, w, e = select.select(i, [], [], 1)
			if self.dev.fileno() in r:
				return self.dev.read()
			if self.readPipe in r:
				try:
					while True:
						t = os.read(self.readPipe, 1)
				except Exception as e:
					pass
			return ''
		finally:
			self.waitingForData = False

	def send(self, msg):
		self.__send(msg)

	def __send(self, msg):
		for c in msg:
			if type(c) == str:
				self.dev.write(c)
			else:
				self.dev.write(chr(c))
