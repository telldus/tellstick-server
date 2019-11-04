# -*- coding: utf-8 -*-

import code
import logging
import os
import signal
import sys
import time
from threading import Thread
import traceback

from base import Application, Plugin, implements
from web.base import IWebRequestAuthenticationHandler

# Get the cwd as soon as possible
_module__file__base = os.getcwd()  # pylint: disable=C0103

class Developer(Plugin):
	implements(IWebRequestAuthenticationHandler)

	def __init__(self):
		self.running = True
		self.mtimes = {}
		self.thread = Thread(target=self.run)
		self.thread.start()
		signal.signal(signal.SIGUSR1, Developer.debugshell)  # Register handler
		Application().registerShutdown(self.stop)

	def checkModifiedFiles(self):
		for filename in Developer.sysfiles():
			oldtime = self.mtimes.get(filename)
			try:
				mtime = os.stat(filename).st_mtime
			except OSError:
				# Probably deleted
				mtime = None
			if oldtime is None:
				# First check
				self.mtimes[filename] = mtime
			elif mtime is None or mtime > oldtime:
				# File was changed or deleted
				logging.info("Restarting because %s changed.", filename)
				Application().quit()

	@staticmethod
	def debugshell(sig, frame):
		"""Interrupt running process, and provide a python prompt for
		interactive debugging."""
		del sig
		localVars = {'_frame': frame}         # Allow access to frame object.
		localVars.update(frame.f_globals)  # Unless shadowed by global
		localVars.update(frame.f_locals)

		i = code.InteractiveConsole(localVars)
		message = "Signal received : entering python shell.\nTraceback:\n"
		message += ''.join(traceback.format_stack(frame))
		i.interact(message)

	def isUrlAuthorized(self, request):  # pylint: disable=R0201
		del request
		return True

	def run(self):
		while self.running:
			try:
				self.checkModifiedFiles()
			except Exception as error:
				exc_type, exc_value, exc_traceback = sys.exc_info()
				del exc_type
				del exc_value
				print(error)
				for file in traceback.extract_tb(exc_traceback):
					print(file)
			time.sleep(1)

	def stop(self):
		self.running = False

	@staticmethod
	def sysfiles():
		files = set()
		for _, module in list(sys.modules.items()):
			if hasattr(module, '__loader__') and hasattr(module.__loader__, 'archive'):
				file = module.__loader__.archive
			else:
				file = getattr(module, '__file__', None)
				if file is not None and not os.path.isabs(file):
					# ensure absolute paths so a os.chdir() in the app
					# doesn't break me
					file = os.path.normpath(os.path.join(_module__file__base, file))
			if file is not None:
				files.add(file)
				if file.endswith('.pyc'):
					file = file[:-1]
					if os.path.exists(file):
						files.add(file)
		return files
