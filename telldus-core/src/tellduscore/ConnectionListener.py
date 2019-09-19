# -*- coding: utf-8 -*-

from base import Application
from .Socket import Socket
from threading import Thread
import os, select, socket

class ConnectionListener(Thread):
	def __init__(self, name, cb):
		super(ConnectionListener,self).__init__()
		self.clients = []
		self.name = name
		self.running = True
		self.cb = cb
		self.start()

	def broadcast(self, *args):
		for client in self.clients:
			client.respond(*args)

	def close(self):
		self.running = False

	def run(self):
		app = Application()
		path = '/tmp/%s' % self.name
		if os.path.exists(path):
			os.remove(path)
		s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
		s.bind(path)
		s.listen(1)
		sockets = [s.fileno()]
		while self.running:
			r, w, e = select.select(sockets, [], [], 10)
			if len(r) == 0:
				continue
			if s.fileno() in r:
				conn, addr = s.accept()
				self.clients.append(Socket(conn))
				sockets.append(conn.fileno())
			for conn in self.clients:
				if conn.fileno() in r:
					d = conn.read()
					if conn.connected:
						app.queue(self.cb, conn, d)
					else:
						sockets.remove(conn.fileno())
			self.clients[:] = [x for x in self.clients if x.connected]
		s.close()
