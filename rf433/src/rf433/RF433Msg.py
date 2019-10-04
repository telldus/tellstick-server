# -*- coding: utf-8 -*-

from base import Application

class RF433Msg(object):

	START = b'S'
	END = b'+'

	def __init__(self, cmd, args = '', prefixes = {}, success=None, failure=None):
		self._cmd = cmd
		self._args = args
		self._prefixes = prefixes
		self._success = success
		self._failure = failure
		self.queued = None

	def cmd(self):
		return self._cmd

	def commandBytes(self):
		if type(self._args) == bytearray:
			# new way using bytearrays, migrate one protocol at a time
			if self._cmd == 'S':
				cmdType = RF433Msg.START
			retval = cmdType + self._args + RF433Msg.END
			for p in self._prefixes:
				retval = p + self._prefixes[p] + retval  # TODO, not tested
			return retval
		retval = '%s%s+' % (self._cmd, self._args)
		for p in self._prefixes:
			retval = '%s%s%s' % (p, chr(self._prefixes[p]), retval)
		return bytearray(retval, 'iso-8859-1')

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
		dataCommand = data[0]
		if dataCommand == 'S':
			return ('S', None)
		if dataCommand == 'N':
			return ('N', None)
		if dataCommand == 'V':
			try:
				version = int(data[1:])
			except:
				return (None, None)
			return ('V', version)
		if dataCommand == 'H':
			return ('H', data[1:])
		if dataCommand == 'W':
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
