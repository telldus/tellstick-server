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

class mainthread(object):  # pylint: disable=C0103
	def __init__(self, f):
		self.__f = f

	def __get__(self, obj, objtype):
		def __call__(*args, **kwargs):
			if threading.currentThread() == Application._mainThread:  # pylint: disable=W0212
				# We are in main thread. Call it directly
				self.__f(obj, *args, **kwargs)
			else:
				# Queue call
				Application().queue(self.__f, obj, *args, **kwargs)
		__call__.__name__ = self.__f.__name__
		# Get the number of whitespaces in the beginning
		docs = self.__f.__doc__ or ''
		indentCount = len(docs) - len(docs.lstrip())
		indent = docs[:indentCount].replace("\n", "")

		__call__.__doc__ = "%s\n\n%s.. note::\n%s    Calls to this method are threadsafe.\n" % (
			docs, indent, indent
		)
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
		super(Application, self).__init__()
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

	@staticmethod
	def defaultContext():
		""":returns: the default context used by the application"""
		return Application().pluginContext

	def registerMaintenanceJobHandler(self, func):
		# (there can be only one...)
		self.maintenanceJobHandler = func
		for job in self.waitingMaintenanceJobs:
			self.maintenanceJobHandler(job)

	def registerMaintenanceJob(self, job):
		if self.maintenanceJobHandler:
			self.maintenanceJobHandler(job)
		else:
			self.waitingMaintenanceJobs.append(job)

	@mainthread
	def registerScheduledTask(self, func, seconds=0, minutes=0, hours=0, days=0, runAtOnce=False,
		strictInterval=False, args=None, kwargs=None):
		r"""
		Register a semi regular scheduled task to run at a predefined interval.
		All calls will be made by the main thread.

		:param func func: The function to be called.

		:param integer seconds: The interval in seconds. Optional.
		:param integer minutes: The interval in minutes. Optional.
		:param integer hours: The interval in hours. Optional.
		:param integer days: The interval in days. Optional.
		:param bool runAtOnce: If the function should be called right away or wait one interval?
		:param bool strictInterval: Set this to True if the interval should be strict. That means if
		  the interval is set to 60 seconds and it was run ater 65 seconds the next run will be in 55
		  seconds.
		:param list args: Any args to be supplied to the function. Supplied as \*args.
		:param dict kwargs: Any keyworded args to be supplied to the function. Supplied as \*\*kwargs.

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
			'func': func,
			'args': args,
			'kwargs': kwargs,
		})

	def registerShutdown(self, func):
		"""
		Register shutdown method. The method func will be called the the server
		shuts down. Use this to clean up resources on shutdown.

		:param func func: A function callback to call when the server shuts down
		"""
		self.shutdown.append(func)

	def run(self, startup=None):
		if startup is None:
			self.__loadPkgResourses()
		else:
			for moduleClass in startup:
				try:
					if issubclass(moduleClass, Plugin):
						moduleClass(self.pluginContext)
					else:
						moduleClass()
				except Exception as error:
					__exc_type, __exc_value, exc_traceback = sys.exc_info()
					logging.error("Could not load %s", str(moduleClass))
					logging.error(str(error))
					Application.printBacktrace(traceback.extract_tb(exc_traceback))
		while 1:
			with self.lock:
				if not self.running:
					break
			(task, args, kwargs) = self.__nextTask()
			if task is None:
				continue
			try:
				task(*args, **kwargs)
			except Exception as error:
				__exc_type, __exc_value, exc_traceback = sys.exc_info()
				logging.error(error)
				Application.printBacktrace(traceback.extract_tb(exc_traceback))
		for func in self.shutdown:
			func()
		return sys.exit(self.exitCode)

	def queue(self, func, *args, **kwargs):
		"""
		Queue a function to be executed later. All tasks in this queue will be
		run by the main thread. This is a thread safe function and can safely be
		used to syncronize with the main thread

		:returns: True if the task was queued
		:returns: False if the server is shutting down
		"""
		if self.__isJoining:
			return False
		self.__taskLock.acquire()
		try:
			self.__tasks.append((func, args, kwargs))
			self.__taskLock.notify()
			return True
		finally:
			self.__taskLock.release()
		return False

	def quit(self, exitCode=0):
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
	def printBacktrace(backtrace):
		for frame in backtrace:
			logging.error(str(frame))

	@staticmethod
	def printException(exception):
		__exc_type, __exc_value, exc_traceback = sys.exc_info()
		logging.error(str(exception))
		Application.printBacktrace(traceback.extract_tb(exc_traceback))

	@staticmethod
	def signal(msg, *args, **kwargs):
		"""Send a global signal to registered slots.
		It is not recommended to call this method directly but instead use the signal decorator.
		Any extra parameters supplied will be forwarded to the slot.

		:param str msg: The signal name
		"""
		signalManager = SignalManager(Application._instance.pluginContext)
		signalManager.sendSignal(msg, *args, **kwargs)

	def __signal(self, signum, frame):
		del frame
		logging.info("Signal %d caught", signum)
		self.quit(1)

	def __loadPkgResourses(self):
		if pkg_resources is None:
			return
		for entry in pkg_resources.working_set.iter_entry_points('telldus.plugins'):
			try:
				moduleClass = entry.load()
			except Exception as error:
				__exc_type, __exc_value, exc_traceback = sys.exc_info()
				logging.error("Could not load %s", str(entry))
				logging.error(str(error))
				Application.printBacktrace(traceback.extract_tb(exc_traceback))
		for entry in pkg_resources.working_set.iter_entry_points('telldus.startup'):
			try:
				moduleClass = entry.load()
				if issubclass(moduleClass, Plugin):
					moduleClass(self.pluginContext)
				else:
					moduleClass()
			except Exception as error:
				__exc_type, __exc_value, exc_traceback = sys.exc_info()
				logging.error("Could not load %s", str(entry))
				logging.error(str(error))
				Application.printBacktrace(traceback.extract_tb(exc_traceback))

	def __nextTask(self):
		self.__taskLock.acquire()
		try:  # pylint: disable=R1702
			while True:
				if self.__isJoining:
					break
				# Check scheduled tasks first
				timestamp = time.time()
				for job in self.scheduledTasks:
					if timestamp >= job['nextRuntime']:
						if job['strictInterval']:
							while job['nextRuntime'] < timestamp:
								job['nextRuntime'] = job['nextRuntime'] + job['interval']
						else:
							job['nextRuntime'] = timestamp + job['interval']
						return (job['fn'], job['args'], job['kwargs'])
				if self.__tasks:
					# There is a task. Return
					break
				# Wait for new task. If no new task, timeout after 60s to check scheduled tasks
				self.__taskLock.wait(60)

			if self.__tasks == []:
				return (None, None, None)
			return self.__tasks.pop(0)
		finally:
			self.__taskLock.release()

from .SignalManager import SignalManager  # pylint: disable=C0413
