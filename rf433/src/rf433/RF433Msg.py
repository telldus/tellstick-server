# -*- coding: utf-8 -*-

from base import Application

class RF433Msg(object):
	def __init__(self, cmd, args = '', prefixes = {}, success=None, failure=None):
		self._cmd = cmd
		self._args = args
		self._prefixes = prefixes
		self._success = success
		self._failure = failure
		self.queued = None

	def cmd(self):
		return self._cmd

	def commandString(self):
		retval = '%s%s+' % (self._cmd, self._args)
		for p in self._prefixes:
			retval = '%s%s%s' % (p, chr(self._prefixes[p]), retval)
		return retval

	def response(self, params):
		if self._success:
			Application().queue(self._success, params)

	def timeout(self):
		if self._failure:
			Application().queue(self._failure)

	@staticmethod
	def parseResponse(data):
		if len(data) < 1:
			return (None, None)
		if data[0] == 'S':
			return ('S', None)
		if data[0] == 'N':
			return ('N', None)
		if data[0] == 'V':
			try:
				version = int(data[1:])
			except:
				return (None, None)
			return ('V', version)
		if data[0] == 'W':
			# Incoming
			lines = data[1:]
			msg = {}
			for x in lines.split(';'):
				line = x.split(':', 1)
				if len(line) != 2:
					continue
				msg[line[0]] = line[1]
			return ('W', msg)
		return (None, None)
