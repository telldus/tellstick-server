# -*- coding: utf-8 -*-

import logging
try:
	import pkg_resources
except ImportError:
	pkg_resources = None
import threading
import time
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

	def __init__(self, run=True):
		if Application._initialized:
			return
		Application._initialized = True
		super(Application,self).__init__()
		self.lock = threading.RLock()
		self.running = True
		self.shutdown = []
		self.scheduledTasks = []
		self.waitingMaintenanceJobs = []
		self.maintenanceJobHandler = None
		self.pluginContext = PluginContext()
		self.__isJoining = False
		self.__tasks = []
		self.__taskLock = threading.Condition(threading.Lock())
		signal.signal(signal.SIGINT, self.__signal)
		signal.signal(signal.SIGTERM, self.__signal)
		Application._mainThread = threading.currentThread()
		if run:
			self.run()

	def registerMaintenanceJobHandler(self, fn):
		# (there can be only one...)
		self.maintenanceJobHandler = fn
		for job in self.waitingMaintenanceJobs:
			self.maintenanceJobHandler(job)

	def registerMaintenanceJob(self, job):
		if self.maintenanceJobHandler:
			self.maintenanceJobHandler(job)
		else:
			self.waitingMaintenanceJobs.append(job)

	@mainthread
	def registerScheduledTask(self, fn, seconds=0, minutes=0, hours=0, days=0, runAtOnce=False, strictInterval=False, args=None, kwargs=None):
		seconds = seconds + (minutes*60) + (hours*3600) + (days*86400)
		nextRuntime = int(time.time())
		if not runAtOnce:
			nextRuntime = nextRuntime + seconds
		if args is None:
			args = []
		if kwargs is None:
			kwargs = {}
		self.scheduledTasks.append({
			'interval': seconds,
			'strictInterval': strictInterval,
			'nextRuntime': nextRuntime,
			'fn': fn,
			'args': args,
			'kwargs': kwargs,
		})

	def registerShutdown(self, fn):
		self.shutdown.append(fn)

	def run(self, startup=None):
		if startup is None:
			self.__loadPkgResourses()
		else:
			for moduleClass in startup:
				try:
					if issubclass(moduleClass, Plugin):
						m = moduleClass(self.pluginContext)
					else:
						m = moduleClass()
				except Exception as e:
					exc_type, exc_value, exc_traceback = sys.exc_info()
					logging.error("Could not load %s", str(moduleClass))
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

	@staticmethod
	def signal(msg, *args, **kwargs):
		signalManager = SignalManager(Application._instance.pluginContext)
		signalManager.signal(msg, *args, **kwargs)

	def __signal(self, signum, frame):
		logging.info("Signal %d caught" % signum)
		self.quit()

	def __loadPkgResourses(self):
		if pkg_resources is None:
			return
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

	def __nextTask(self):
		self.__taskLock.acquire()
		try:
			# Check scheduled tasks first
			ts = time.time()
			for job in self.scheduledTasks:
				if ts >= job['nextRuntime']:
					if job['strictInterval']:
						while job['nextRuntime'] < ts:
							job['nextRuntime'] = job['nextRuntime'] + job['interval']
					else:
						job['nextRuntime'] = ts + job['interval']
					return (job['fn'], job['args'], job['kwargs'])
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

from SignalManager import SignalManager
