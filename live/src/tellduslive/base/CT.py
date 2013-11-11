# -*- coding: utf-8 -*-

import threading

class CT(threading.Thread):
	def __init__(self):
		self.start()

	def run(self):
		self.c = Client()

	def stop(self):
		self.c.stop()
