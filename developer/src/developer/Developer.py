# -*- coding: utf-8 -*-

from base import Application, Plugin
from threading import Thread
import os, re, sys, time, traceback

# Get the cwd as soon as possible
_module__file__base = os.getcwd()

class Developer(Plugin):
	def __init__(self):
		self.running = True
		self.mtimes = {}
		self.thread = Thread(target=self.run).start()
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

	def stop(self):
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
