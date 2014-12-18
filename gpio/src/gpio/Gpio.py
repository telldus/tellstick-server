# -*- coding: utf-8 -*-

from base import Plugin
import logging, os

class Gpio(Plugin):
	def __init__(self):
		super(Plugin,self).__init__()

	def initPWM(self, name):
		if os.path.exists('/sys/class/pwm/%s' % name) == False:
			return
		self.__writeToFile('/sys/class/pwm/%s/request' % name, '1')
		self.__writeToFile('/sys/class/pwm/%s/run' % name, '1')
		self.__writeToFile('/sys/class/pwm/%s/period_freq' % name, '100')
		self.__writeToFile('/sys/class/pwm/%s/duty_percent' % name, '0')

	def setPWM(self, name, freq=None, duty=None):
		self.__writeToFile('/sys/class/pwm/%s/run' % name, '0')
		self.__writeToFile('/sys/class/pwm/%s/duty_percent' % name, '0')
		self.__writeToFile('/sys/class/pwm/%s/period_freq' % name, '100')
		if duty is not None:
			self.__writeToFile('/sys/class/pwm/%s/duty_percent' % name, str(duty))
		if freq is not None:
			self.__writeToFile('/sys/class/pwm/%s/period_freq' % name, str(freq))
		self.__writeToFile('/sys/class/pwm/%s/run' % name, '1')

	def __writeToFile(self, path, value):
		try:
			with open(path, 'w') as f:
				f.write(value)
		except:
			pass
