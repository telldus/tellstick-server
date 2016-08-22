# -*- coding: utf-8 -*-

from base import Application, Plugin
from rf433 import RF433, RF433Msg

from threading import Timer

class Emc(Plugin):
	def __init__(self):
		Application().registerShutdown(self.__stop)
		self.running = True
		# Delay start to let everything load properly
		Timer(10.0, self.resend).start()

	def __stop(self):
		self.running = False

	def resend(self, *args, **kwargs):
		if not self.running:
			return
		Application().queue(self.send433)

	def send433(self):
		msg = '$k$k$k$k$k$k$k$k$k$k$k$k$k$k$k$k$k$k$kk$$kk$$kk$$}'
		rf433 = RF433(self.context)
		rf433.dev.queue(RF433Msg('S', msg, {}, success=self.resend, failure=self.resend))
