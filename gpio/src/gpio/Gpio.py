# -*- coding: utf-8 -*-

from base import Plugin, Application
from board import Board
from threading import Thread
import logging, os, time

class Pin(Thread):
	def __init__(self):
		super(Pin,self).__init__()
		self.state = None  # Unknown
		self.brightness = None
		self.freq = 0

	def run(self):
		s = 0
		while(self.freq > 0):
			s = 1-s
			self._setState(s)
			time.sleep(self.freq)
		# Makes it possible for us to restart this thread
		Thread.__init__(self)

	def setPin(self, state, freq = 0, brightness = 100):
		if self.brightness != brightness:
			self._setBrigtness(brightness)
			self.brightness = brightness
		if self.state == state:
			if self.freq != freq:
				if self.freq == 0:
					self.freq = freq
					self.start()
				else:
					self.freq = freq
				if freq == 0:
					self._setState(self.state)
			return
		self.state = state
		if state == 0:
			# Stop timer if running
			if self.freq > 0:
				self.freq = 0
			self._setState(state)
			return
		if freq > 0:
			# Blink
			self.freq = freq
			self.start()
			return
		self.freq = 0
		self._setState(state)

	def _setBrigtness(self, brightness):
		logging.warning("Set brightness not implemented")

	def _setState(self, state):
		logging.warning("State not implemented")

	def _writeToFile(self, path, value):
		try:
			with open(path, 'w') as f:
				f.write(value)
		except:
			pass

class GpioPin(Pin):
	def __init__(self, pin):
		super(GpioPin,self).__init__()
		self.pin = pin
		if os.path.exists('/sys/class/gpio/gpio%s' % pin['port']) == False:
			if os.path.exists('/sys/class/gpio/export') == False:
				return
			# Export the gpio
			self._writeToFile('/sys/class/gpio/export', pin['port'])
		if os.path.exists('/sys/class/gpio/gpio%s' % pin['port']) == False:
			logging.error('Gpio not available even though it is exported. Something is wrong!')
			return
		self._writeToFile('/sys/class/gpio/gpio%s/direction' % pin['port'], 'out')

	def _setBrigtness(self, brightness):
		return  # No PWM available for gpio pins

	def _setState(self, state):
		if state == 1:
			self._writeToFile('/sys/class/gpio/gpio%s/value' % self.pin['port'], '1')
		else:
			self._writeToFile('/sys/class/gpio/gpio%s/value' % self.pin['port'], '0')

class LedPin(Pin):
	def __init__(self, pin):
		super(LedPin,self).__init__()
		self.pin = pin

	def _setBrigtness(self, brightness):
		return  # No PWM available for led pins

	def _setState(self, state):
		if state == 1:
			self._writeToFile('/sys/class/leds/%s/brightness' % self.pin['port'], '1')
		else:
			self._writeToFile('/sys/class/leds/%s/brightness' % self.pin['port'], '0')

class PWMPin(Pin):
	def __init__(self, pin):
		super(PWMPin,self).__init__()
		self.pin = pin
		if os.path.exists('/sys/class/pwm/%s' % pin['port']) == False:
			return
		self._writeToFile('/sys/class/pwm/%s/request' % pin['port'], '1')
		self._writeToFile('/sys/class/pwm/%s/run' % pin['port'], '1')
		self._writeToFile('/sys/class/pwm/%s/period_freq' % pin['port'], '100')
		self._writeToFile('/sys/class/pwm/%s/duty_percent' % pin['port'], '0')

	def _setBrigtness(self, brightness):
		return  # TODO(micke): Not implemented yet

	def _setState(self, state):
		self._writeToFile('/sys/class/pwm/%s/run' % self.pin['port'], '0')
		self._writeToFile('/sys/class/pwm/%s/duty_percent' % self.pin['port'], '0')
		self._writeToFile('/sys/class/pwm/%s/period_freq' % self.pin['port'], '100')
		if state == 1:
			self._writeToFile('/sys/class/pwm/%s/duty_percent' % self.pin['port'], '100')
		else:
			self._writeToFile('/sys/class/pwm/%s/duty_percent' % self.pin['port'], '0')
		self._writeToFile('/sys/class/pwm/%s/run' % self.pin['port'], '1')

class Gpio(Plugin):
	def __init__(self):
		super(Plugin,self).__init__()
		Application().registerShutdown(self.shutdown)
		self.pins = {}

	def initPin(self, name):
		config = Board.gpioConfig()
		if name not in config:
			logging.warning('GPIO %s not configured in board config', name)
			return False
		pin = config[name]
		if name in self.pins:
			# Already initiated
			return True
		if pin['type'] == 'gpio':
			self.pins[name] = GpioPin(pin)
		elif pin['type'] == 'led':
			self.pins[name] = LedPin(pin)
		elif pin['type'] == 'pwm':
			self.pins[name] = PWMPin(pin)
		elif pin['type'] == 'none':
			# We don't have this pin on the board but is configured to not issue an warning
			return False
		return True

	def setPin(self, name, state, freq = 0, brightness = 100):
		if name not in self.pins:
			return False
		self.pins[name].setPin(state, freq, brightness)

	async def shutdown(self):
		for i in self.pins:
			self.pins[i].setPin(0)
