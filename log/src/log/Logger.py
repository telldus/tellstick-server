# -*- coding: utf-8 -*-

from base import Plugin
import logging, sys, time, os
import logging.config, logging.handlers

class PrintCollector(object):
	def __init__(self, stream):
		self.buffer = ''
		self.stream = stream

	def flush(self):
		pass

	def write(self, data, *args, **kwargs):
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
		if (record.levelno == logging.DEBUG):
			record.levelname = 'DBG'
		elif (record.levelno == logging.INFO):
			record.levelname = 'INF'
		elif (record.levelno == logging.INFO+5):
			record.levelname = 'LOG'
		elif (record.levelno == logging.WARNING):
			record.levelname = 'WRN'
		elif (record.levelno == logging.ERROR):
			record.levelname = 'ERR'
		elif (record.levelno == logging.CRITICAL):
			record.levelname = 'CRI'

		logstring =  "[%s] %s (%s) %s" % (record.levelname, time.strftime("%H:%M:%S", time.localtime()), record.name, record.getMessage())
		return logstring

class Logger(Plugin):
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
