# -*- coding: utf-8 -*-

import os
import json
import logging
import time
from .Application import Application
from configobj import ConfigObj
from threading import Timer
from board import Board
from six.moves.configparser import ConfigParser

class Settings(object):
	_config = None
	_lastWrite = None
	_writeTimer = None

	def __init__(self, section):
		super(Settings,self).__init__()
		self.section = section

		if Settings._config is None:
			self.configPath = Board.configDir()
			if not os.path.exists(self.configPath):
				os.makedirs(self.configPath)
			self.configFilename = 'Telldus.conf'
			self.__loadFile()
			Application().registerShutdown(self.__shutdown)
		if section not in Settings._config:
			Settings._config[section] = {}

	def get(self, name, default):
		v = self[name]
		if v is None:
			return default
		if type(default) is dict or type(default) is list:
			v = json.loads(v)
		if type(default) == int:
			v = int(v)
		return v

	def __loadFile(self):
		try:
			Settings._config = ConfigObj(self.configPath + '/' + self.configFilename)
		except:
			logging.critical('Could not load settings file!')
			# Start with empty one
			Settings._config = ConfigObj()
			Settings._config.filename = self.configPath + '/' + self.configFilename

	def __shutdown(self):
		if Settings._writeTimer is not None:
			Settings._writeTimer.cancel()
			self.__writeTimeout()

	def __writeTimeout(self):
		Settings._writeTimer = None
		Settings._lastWrite = time.time()
		Settings._config.write()

	def __writeToDisk(self):
		if Settings._writeTimer is not None:
			return
		if Settings._lastWrite is None or (time.time() - Settings._lastWrite) > 300:
			Settings._writeTimer = Timer(1.0, self.__writeTimeout)
		else:
			Settings._writeTimer = Timer(300.0, self.__writeTimeout)
		Settings._writeTimer.start()

	def __getitem__(self, name):
		try:
			value = Settings._config[self.section][name]
		except:
			return None
		return value

	def __setitem__(self, name, value):
		if type(value) is dict or type(value) is list:
			value = json.dumps(value)
		Settings._config[self.section][name] = value
		self.__writeToDisk()
