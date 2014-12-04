# -*- coding: utf-8 -*-

import logging
import pkg_resources
import threading
import traceback
import signal
import sys
from Plugin import Plugin, PluginContext

# Decorator
class mainthread(object):
	def __init__(self, f):
		self.__f = f

	def __get__(self, obj, objtype):
		def __call__(*args, **kwargs):
			if threading.currentThread() == Application._mainThread:
				# We are in main thread. Call it directly
				self.__f(obj, *args, **kwargs)
			else:
				# Queue call
				Application().queue(self.__f, obj, *args, **kwargs)
			return None
		return __call__

class Application(object):
	_instance = None
	_initialized = False
	_mainThread = None

	def __new__(cls, *args, **kwargs):
		if not cls._instance:
			cls._instance = super(Application, cls).__new__(cls, *args, **kwargs)
		return cls._instance

	def __init__(self):
		if Application._initialized:
			return
		Application._initialized = True
		super(Application,self).__init__()
		self.lock = threading.RLock()
		self.running = True
		self.shutdown = []
		self.pluginContext = PluginContext()
		self.__isJoining = False
		self.__tasks = []
		self.__taskLock = threading.Condition(threading.Lock())
		signal.signal(signal.SIGINT, self.signal)
		signal.signal(signal.SIGTERM, self.signal)
		Application._mainThread = threading.currentThread()
		self.run()

	def registerShutdown(self, fn):
		self.shutdown.append(fn)

	def run(self):
		for entry in pkg_resources.working_set.iter_entry_points('telldus.plugins'):
			try:
				moduleClass = entry.load()
			except Exception as e:
				exc_type, exc_value, exc_traceback = sys.exc_info()
				logging.error("Could not load %s", str(entry))
				logging.error(str(e))
				self.printBacktrace(traceback.extract_tb(exc_traceback))
		for entry in pkg_resources.working_set.iter_entry_points('telldus.startup'):
			try:
				moduleClass = entry.load()
				if issubclass(moduleClass, Plugin):
					m = moduleClass(self.pluginContext)
				else:
					m = moduleClass()
			except Exception as e:
				exc_type, exc_value, exc_traceback = sys.exc_info()
				logging.error("Could not load %s", str(entry))
				logging.error(str(e))
				self.printBacktrace(traceback.extract_tb(exc_traceback))
		while 1:
			with self.lock:
				if not self.running:
					break
			(task, args, kwargs) = self.__nextTask()
			if task == None:
				continue
			try:
				task(*args, **kwargs)
			except Exception as e:
				exc_type, exc_value, exc_traceback = sys.exc_info()
				logging.error(e)
				self.printBacktrace(traceback.extract_tb(exc_traceback))
		for fn in self.shutdown:
			fn()
	
	def queue(self, fn, *args, **kwargs):
		if self.__isJoining == True:
			return False
		self.__taskLock.acquire()
		try:
			self.__tasks.append((fn, args, kwargs))
			self.__taskLock.notify()
			return True
		finally:
			self.__taskLock.release()
		return False

	def quit(self):
		with self.lock:
			self.running = False
			self.__isJoining = True

		self.__taskLock.acquire()
		try:
			self.__taskLock.notifyAll()
		finally:
			self.__taskLock.release()

	def printBacktrace(self, bt):
		for f in bt:
			logging.error(str(f))

	def signal(self, signum, frame):
		logging.info("Signal %d caught" % signum)
		self.quit()

	def __nextTask(self):
		self.__taskLock.acquire()
		try:
			while len(self.__tasks) == 0:
				if (self.__isJoining == True):
					break
				self.__taskLock.wait(60)

			if self.__tasks == []:
				return (None, None, None)
			else:
				return self.__tasks.pop(0)
		finally:
			self.__taskLock.release()
