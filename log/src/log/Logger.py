# -*- coding: utf-8 -*-

from base import Plugin
import logging, sys, time

class PrintCollector(object):
	def __init__(self, stdout):
		self.stdout = stdout
		self.buffer = ''

	def write(self, data, *args, **kwargs):
		if data == "\n":
			logging.debug(self.buffer)
			self.buffer = ''
		else:
			self.buffer = self.buffer + data

class Logger(Plugin):
	def __init__(self):
		self.p = PrintCollector(sys.stdout)
		self.l = Log(sys.stdout)
		sys.stdout = self.p
		logger = logging.getLogger()
		logger.setLevel(logging.DEBUG)
		logger.addHandler(self.l)

class Log(logging.Handler):
	def __init__(self, stdout):
		super(Log,self).__init__()
		self.stdout = stdout

	def handle(self, record):
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

		logstring =  "[%s] %s %s" % (record.levelname, time.strftime("%H:%M:%S", time.localtime()), record.getMessage())
		print >> self.stdout, logstring
