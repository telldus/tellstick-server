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
from .Plugin import Plugin, PluginContext

class mainthread(object):
	""".. py:decorator:: mainthread

	This decorator forces a method to be run in the main thread regardless of
	which thread calls the method."""
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
		__call__.__name__ = self.__f.__name__
		__call__.__doc__ = "%s\n\n.. note::\n    Calls to this method are threadsafe.\n" % self.__f.__doc__
		return __call__

class Application(object):
	"""
	This is the main application object in the server. There can only be once
	instance of this object. The default constructor returns the instance of this
	object.
	"""
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
		self.exitCode = 0
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
		"""
		Register a semi regular scheduled task to run at a predefined interval.
		All calls will be made by the main thread.

		  :fn: The function to be called.
		  :seconds: The interval in seconds. Optional.
		  :minutes: The interval in minutes. Optional.
		  :hours: The interval in hours. Optional.
		  :days: The interval in days. Optional.
		  :runAtOnce: If the function should be called right away or wait one interval?
		  :strictInterval: Set this to True if the interval should be strict. That means if the interval is set to 60 seconds and it was run ater 65 seconds the next run will be in 55 seconds.
		  :args: Any args to be supplied to the function. Supplied as \*args.
		  :kwargs: Any keyworded args to be supplied to the function. Supplied as \*\*kwargs.

		.. note::
		    The interval in which this task is run is not exact and can be delayed
		    one minute depending on the server load.

		"""
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
		"""Register shutdown method. The method fn will be called the the server
		shuts down. Use this to clean up resources on shutdown."""
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
					Application.printBacktrace(traceback.extract_tb(exc_traceback))
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
				Application.printBacktrace(traceback.extract_tb(exc_traceback))
		for fn in self.shutdown:
			fn()
		return sys.exit(self.exitCode)

	def queue(self, fn, *args, **kwargs):
		"""Queue a function to be executed later. All tasks in this queue will be
		run by the main thread. This is a thread safe function and can safely be
		used to syncronize with the main thread"""
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

	def quit(self, exitCode = 0):
		with self.lock:
			self.running = False
			self.exitCode = exitCode
			self.__isJoining = True

		self.__taskLock.acquire()
		try:
			self.__taskLock.notifyAll()
		finally:
			self.__taskLock.release()

	@staticmethod
	def printBacktrace(bt):
		for f in bt:
			logging.error(str(f))

	@staticmethod
	def printException(exception):
		exc_type, exc_value, exc_traceback = sys.exc_info()
		logging.error(str(exception))
		Application.printBacktrace(traceback.extract_tb(exc_traceback))

	@staticmethod
	def signal(msg, *args, **kwargs):
		"""Send a global signal to registered slots.
		It is not recommended to call this method directly but instead use the signal decorator
		"""
		signalManager = SignalManager(Application._instance.pluginContext)
		signalManager.sendSignal(msg, *args, **kwargs)

	def __signal(self, signum, frame):
		logging.info("Signal %d caught" % signum)
		self.quit(1)

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
				Application.printBacktrace(traceback.extract_tb(exc_traceback))
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
				Application.printBacktrace(traceback.extract_tb(exc_traceback))

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

from .SignalManager import SignalManager
