# -*- coding: utf-8 -*-

import logging

class Socket(object):
	def __init__(self, conn):
		super(Socket,self).__init__()
		self.conn = conn
		self.connected = True

	def fileno(self):
		return self.conn.fileno()

	def read(self):
		try:
			d = self.conn.recv(1024)
		except:
			self.connected = False
			return ''
		if d == '':
			self.connected = False
		return d

	def respond(self, *args):
		msg = ''
		for value in args:
			if type(value) is int:
				msg = msg + 'i%is' % value
			elif type(value) is str:
				msg = msg + '%i:%s' % (len(value), value)
			elif type(value) is unicode:
				value = value.encode('utf-8')
				msg = msg + '%i:%s' % (len(value), value)
			else:
				logging.warning("Unknown type to encode %s", type(value))
				return
		self.write(msg)

	def write(self, msg):
		self.conn.send(msg)
