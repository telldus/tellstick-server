# -*- coding: utf-8 -*-

from base import Application, Plugin, implements
from web.base import IWebRequestAuthenticationHandler
from threading import Thread
import os, re, sys, time, traceback
import code, signal
import asyncio

# Get the cwd as soon as possible
_module__file__base = os.getcwd()

class Developer(Plugin):
	implements(IWebRequestAuthenticationHandler)

	def __init__(self):
		self.running = True
		self.mtimes = {}
		self.thread = Thread(target=self.run).start()
		signal.signal(signal.SIGUSR1, self.debugshell)  # Register handler
		asyncio.get_event_loop().set_debug(True)
		Application().registerShutdown(self.stop)

	def checkModifiedFiles(self):
		for filename in self.sysfiles():
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
				print("Restarting because %s changed." % filename)
				Application().quit()

	def debugshell(self, sig, frame):
		"""Interrupt running process, and provide a python prompt for
		interactive debugging."""
		d={'_frame':frame}         # Allow access to frame object.
		d.update(frame.f_globals)  # Unless shadowed by global
		d.update(frame.f_locals)

		i = code.InteractiveConsole(d)
		message  = "Signal received : entering python shell.\nTraceback:\n"
		message += ''.join(traceback.format_stack(frame))
		i.interact(message)

	def isUrlAuthorized(self, request):
		return True

	def run(self):
		while self.running:
			try:
				self.checkModifiedFiles()
			except Exception as e:
				exc_type, exc_value, exc_traceback = sys.exc_info()
				print(e)
				for f in traceback.extract_tb(exc_traceback):
					print(f)
			time.sleep(1)

	async def stop(self):
		self.running = False

	def sysfiles(self):
		files = set()
		for k, m in list(sys.modules.items()):
			if hasattr(m, '__loader__') and hasattr(m.__loader__, 'archive'):
				f = m.__loader__.archive
			else:
				f = getattr(m, '__file__', None)
				if f is not None and not os.path.isabs(f):
					# ensure absolute paths so a os.chdir() in the app
					# doesn't break me
					f = os.path.normpath(os.path.join(_module__file__base, f))
			if f is not None:
				files.add(f)
				if f.endswith('.pyc'):
					f = f[:-1]
					if os.path.exists(f):
						files.add(f)
		return files
