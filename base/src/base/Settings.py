# -*- coding: utf-8 -*-

import os
from configobj import ConfigObj
import ConfigParser


class Settings(object):
	def __init__(self, section):
		super(Settings,self).__init__()
		self.section = section

		self.configPath = os.environ['HOME'] + '/.config/Telldus'
		self.configFilename = 'Telldus.conf'
		self.config = ConfigObj(self.configPath + '/' + self.configFilename)

	def __getitem__(self, name):
		try:
			value = self.config[self.section]
		except:
			return None
		return value

	def __setitem__(self, name, value):
		self.config[self.section] = value
		self.config.write()
