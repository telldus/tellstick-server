# -*- coding: utf-8 -*-

from base import Application
import fcntl, os, select, serial, threading, time
from RF433Msg import RF433Msg
import logging
try:
	from pkg_resources import resource_filename
except ImportError:
	# pkg_resources not available, load firmware from filesystem
	def resource_filename(module, filename):
		raise Exception("Loading of firmware not implemented yet")

class Adapter(threading.Thread):
	BOOTLOADER_START = 0x7A00

	def __init__(self, handler, dev):
		super(Adapter,self).__init__()
		self.handler = handler
		self.__queue = []
		self.__waitForResponse = None
		self.__setupHardware()
		self.waitingForData = False
		try:
			self.dev = serial.serial_for_url(dev, 115200, timeout=0)
		except Exception as e:
			logging.error("Could not open serial port: %s", e)
			self.dev = None
		Application().registerShutdown(self.__stop)
		(self.readPipe, self.writePipe) = os.pipe()
		fl = fcntl.fcntl(self.readPipe, fcntl.F_GETFL)
		fcntl.fcntl(self.readPipe, fcntl.F_SETFL, fl | os.O_NONBLOCK)
		self.requireUpdate = False
		if self.dev is not None:
			self.start()

	def queue(self, msg):
		self.__queue.append(msg)
		if self.waitingForData:
			# Abort current read
			os.write(self.writePipe, 'w')

	def run(self):
		self.running = True
		app = Application()
		buffer = ''
		ttl = None
		state = 0

		while self.running:
			if self.requireUpdate and state == 0:
				self.requireUpdate = False
				state = 2

			if state == 0:
				x = self.__readByte(interruptable=True)
				if x == '':
					if self.__waitForResponse is not None and self.__waitForResponse.queued + 3 < time.time():
						self.__waitForResponse.timeout()
						self.__waitForResponse = None
					if len(self.__queue) and self.__waitForResponse is None:
						state = 1
					continue
				if x == '\r':
					continue
				if x == '+':
					# Start of data
					buffer = ''
					continue
				if x == '\n':
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
				self.__send(self.__waitForResponse.commandString())
				self.__waitForResponse.queued = time.time()
				state = 0

			elif state == 2:  # Flash new firmware
				firmware = self.__loadFirmware()
				if firmware is None:
					logging.error('Could not load firmware for RF433')
					state = 0
					continue
				app.queue(self.__enterBootloader)
				ttl = time.time() + 3  # 3 second timeout
				state = 3
			elif state == 3:  # Wait for bootloader
				x = self.__readByte(interruptable=True)
				if x == 'g':
					self.__send('r')
					state = 4
					continue
				if time.time() > ttl:
					# Timeout
					logging.warning("Timeout trying to enter bootloader")
					state = 0
			elif state == 4:  # In bootloader
				self.__uploadFirmware(firmware)
				logging.info("Firmware updated!")
				firmware = None
				state = 0

	def updateFirmware(self):
		self.requireUpdate = True

	def __enterBootloader(self):
		if os.path.exists('/sys/class/gpio/gpio5') == False:
			logging.error('Cannot enter bootloader, no reset signal available')
			return
		with open('/sys/class/gpio/gpio5/value', 'w') as f:
			f.write('1')
		time.sleep(0.1)
		with open('/sys/class/gpio/gpio5/value', 'w') as f:
			f.write('0')

	def __loadFirmware(self):
		data = []
		try:
			f = open(resource_filename('rf433', 'firmware/TellStickDuo.hex'), 'r')
		except Exception as e:
			logging.error(e)
			return None
		for line in f.readlines():
			line = line.strip()
			if len(line) < 11 or line[0] != ':':
				# skip line if not hex line entry,or not minimum length ":BBAAAATTCC"
				continue
			try:
				byteCount = int(line[1:3], 16)
				startAddress = int(line[3:7], 16)
				recordType = int(line[7:9], 16)
				if recordType == 0x01:  # End of file
					break
				elif recordType == 0x02:  # Extended Segment Address Record. Not implemented
					pass
				elif recordType == 0x04:  # Extended Linear Address Record. Not supported
					pass
				elif recordType == 0x00:  # Data record
					record = line[9:-2]
					if len(record) != byteCount*2:
						logging.error("Wrong length on line in hex-file")
						return None
					# Protect us from overwriting the bootloader
					if startAddress >= Adapter.BOOTLOADER_START:
						continue
					# Pad with empty data when needed
					if startAddress > len(data):
						while startAddress > len(data):
							data.append(0xFF)
					for i in range(byteCount):
						o = i*2
						data.append(int(record[o:o+2], 16))
			except Exception as e:
				logging.error("Could not parse hex-file: %s", str(e))
				return None
		# Pad at least 64-bytes extra so the last block will be written to the memory
		for i in range(64):
			data.append(0xFF)
		return data

	def __setupHardware(self):
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

	def __stop(self):
		self.running = False
		if self.waitingForData:
			# Abort current read
			os.write(self.writePipe, 'w')

	def __uploadFirmware(self, firmware):
		while True:
			x = self.__readByte()
			if x == '':
				continue
			if x == 'b':
				bytesLeft = len(firmware)
				if bytesLeft > 0xFF:
					bytesLeft = 0xFF
				self.__send([bytesLeft])
				if bytesLeft == 0:
					logging.info("Firmware uploaded completely!")
					break
			elif x == 'd':
				if len(firmware) == 0:
					logging.error("Tried to retrieve data past end of file")
					break
				d = firmware.pop(0)
				self.__send([d])

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

	def __send(self, msg):
		for c in msg:
			if type(c) == str:
				self.dev.write(c)
			else:
				self.dev.write(chr(c))
