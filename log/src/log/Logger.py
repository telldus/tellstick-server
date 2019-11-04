# -*- coding: utf-8 -*-

import logging
import logging.config
import os
import sys
import time

from base import Plugin

class PrintCollector(object):
	def __init__(self, stream):
		self.buffer = ''
		self.stream = stream

	def flush(self):
		pass

	def write(self, data, *__args, **__kwargs):
		if data == "\n":
			if self.stream == 'stderr':
				logging.error(self.buffer)
			else:
				logging.debug(self.buffer)
			self.buffer = ''
		else:
			self.buffer = self.buffer + data

class LogFormatter(logging.Formatter):
	def format(self, record):
		formatString = ''
		if (record.levelno == logging.DEBUG):
			formatString = '\033[1;32m'  # Bold (1) + White (37)
			record.levelname = 'DBG'
		elif (record.levelno == logging.INFO):
			record.levelname = 'INF'
		elif (record.levelno == logging.INFO+5):
			record.levelname = 'LOG'
		elif (record.levelno == logging.WARNING):
			record.levelname = 'WRN'
			formatString = '\033[33m'  # Yellow (33)
		elif (record.levelno == logging.ERROR):
			formatString = '\033[31m'  # Red (31)
			record.levelname = 'ERR'
		elif (record.levelno == logging.CRITICAL):
			formatString = '\033[1;41m'  # Bold (1) + Red backround (41)
			record.levelname = 'CRI'

		logstring = "%s[%s] %s (%s) %s\033[0m" % (
			formatString,
			record.levelname,
			time.strftime("%H:%M:%S", time.localtime()),
			record.name,
			record.getMessage()
		)
		return logstring

class Logger(Plugin):
	def __init__(self):
		if os.environ.get('DEFAULT_LOG_HANDLER') == 'syslog':
			defaultLogHandler = {
				'level':'DEBUG',
				'class':'logging.handlers.SysLogHandler',
				'formatter': 'standard',
				'address': '/dev/log'
			}
		else:
			defaultLogHandler = {
				'level':'DEBUG',
				'class':'logging.StreamHandler',
				'formatter': 'standard',
				'stream': 'ext://sys.__stdout__'
			}

		logging.config.dictConfig({
			'version': 1,
			'formatters': {
				'standard': {
					'()': LogFormatter,
				},
			},
			'handlers': {
				'default': defaultLogHandler,
			},
			'loggers': {
				'': {
					'handlers': ['default'],
					'level': 'DEBUG'
				},
				'cherrypy.access': {
					'propagate': True
				},
				'cherrypy.error': {
					'propagate': True
				},
			}
		})

		sys.stdout = PrintCollector('stdout')
		sys.stderr = PrintCollector('stderr')
