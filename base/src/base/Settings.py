# -*- coding: utf-8 -*-

import os
import json
from configobj import ConfigObj
from board import Board
import ConfigParser


class Settings(object):
	_config = None

	def __init__(self, section):
		super(Settings,self).__init__()
		self.section = section

		if Settings._config is None:
			self.configPath = Board.configDir()
			if not os.path.exists(self.configPath):
				os.makedirs(self.configPath)
			self.configFilename = 'Telldus.conf'
			Settings._config = ConfigObj(self.configPath + '/' + self.configFilename)
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
		Settings._config.write()
