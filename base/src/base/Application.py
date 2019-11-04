# -*- coding: utf-8 -*-

import asyncio
import functools
import inspect
import logging
import os
try:
	import pkg_resources
except ImportError:
	pkg_resources = None
import threading
import time
import traceback
from typing import Any, Callable
import signal
import sys
from .Plugin import Plugin, PluginContext

async def asyncWrapper(func, *args, **kwargs):
	return func(*args, **kwargs)

class mainthread(object):
	def __init__(self, f):
		self.__f = f

	async def __asyncWrapper(self, obj, *args, **kwargs):
		if not Application.isMainThread():
			logging.critical('Something went wrong when syncing call with main thread.')
			logging.critical('This should not be possible!')
			return None
		# We are now in main thread. Call the function
		self.__f(obj, *args, **kwargs)

	def __get__(self, obj, objtype):
		def __call__(*args, **kwargs):
			if Application.isMainThread():
				# We are in main thread. Call it directly
				self.__f(obj, *args, **kwargs)
			else:
				# Queue call
				if inspect.iscoroutinefunction(self.__f):
					Application().queue(self.__f, obj, *args, **kwargs)
				else:
					# Non async function. Call blocking from main thread.
					# To do this we must wrap it in an async function.
					Application().queue(self.__asyncWrapper, obj, *args, **kwargs)

		__call__.__name__ = self.__f.__name__
		# Get the number of whitespaces in the beginning
		docs = self.__f.__doc__ or ''
		indentCount = len(docs) - len(docs.lstrip())
		indent = docs[:indentCount].replace("\n", "")

		__call__.__doc__ = "%s\n\n%s.. note::\n%s    Calls to this method are threadsafe.\n" % (
			docs, indent, indent
		)
		return __call__

def callback(func):
	"""
	Decorator for non async function to be safe to call from the main thread.
	This means they will not block.
	"""
	func.__callbackSafe__ = True
	return func

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
		signal.signal(signal.SIGINT, self.__signal)
		signal.signal(signal.SIGTERM, self.__signal)
		Application._mainThread = threading.currentThread()
		self.loop = asyncio.get_event_loop()
		self.loop.set_exception_handler(self.exceptionHandler)
		self.shutdownEvent = asyncio.Event()
		if run:
			self.run()

	def createTask(self, cbFn: Callable[..., Any], *args, **kwargs):
		"""Creates a task to run in the event loop.

		If the target is not a coroutine this will be executed in a thread pool allowing for
		blocking method to be used. Please make sure proper thread saftey in such metods if they
		call functions expected to be called from the main thread. Please see
		:func:`Application.queue()` for ways to syncronize with the main
		event loop.

		:param Callable[...,Any] cbFn: The target function to run
		:since: 2.0

		.. note::
			Calls to this method are threadsafe.
		"""
		self.loop.call_soon_threadsafe(self.asyncCreateTask, cbFn, *args, **kwargs)

	def asyncCreateTask(self, cbFn: Callable[..., Any], *args, **kwargs):
		"""Creates a task to run in the event loop.

		This method is not threadsafe and must be called from the main event loop.
		See :func:`Application.createTask()` for a threadsafe version.

		:since: 2.0
		"""
		unwrappedFn = cbFn
		# The target may be a partial which means we cannot check the type without getting the
		# actual function
		while isinstance(unwrappedFn, functools.partial):
			unwrappedFn = unwrappedFn.func

		if inspect.iscoroutinefunction(unwrappedFn):
			#self.loop.create_task()  # From Python 3.7
			task = asyncio.ensure_future(cbFn(*args, **kwargs))
		else:
			# Not compatible with asyncio. May be blocking. Run in own thread.
			syncWrapper = self.loop.run_in_executor(None, functools.partial(cbFn, *args, **kwargs))
			task = asyncio.ensure_future(syncWrapper)

	@staticmethod
	def defaultContext():
		""":returns: the default context used by the application"""
		return Application().pluginContext

	@staticmethod
	def exceptionHandler(__loop, context):
		logger = logging.getLogger(__name__)
		logger.error('Exception happened in task: "%s", at:', str(context['exception']))
		#print(context['future'].get_coro())  Added in python 3.8
		for frame in reversed(context['future'].get_stack()):
			code = frame.f_code
			prefix = os.path.commonpath([__file__, code.co_filename])
			logger.error(
				'\t%s() in %s, line %s',
				code.co_name,
				code.co_filename[len(prefix)+1:],
				frame.f_lineno
			)

	@staticmethod
	def isMainThread():
		"""
		Query if the current thread is the main thread.

		:returns: True if the call was made from the main thread, False otherwise.
		:since: 2.0
		"""
		return threading.current_thread() is Application._mainThread

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

		:param func fn: The function to be called.

		:param integer seconds: The interval in seconds. Optional.
		:param integer minutes: The interval in minutes. Optional.
		:param integer hours: The interval in hours. Optional.
		:param integer days: The interval in days. Optional.
		:param bool runAtOnce: If the function should be called right away or wait one interval?
		:param bool strictInterval: Set this to True if the interval should be strict. That means if the interval is set to 60 seconds and it was run ater 65 seconds the next run will be in 55 seconds.
		:param list args: Any args to be supplied to the function. Supplied as \*args.
		:param dict kwargs: Any keyworded args to be supplied to the function. Supplied as \*\*kwargs.

		:returns: A task object that can be used to cancel the scheduled task
		"""
		seconds = seconds + (minutes*60) + (hours*3600) + (days*86400)
		nextRuntime = int(self.loop.time())
		if not runAtOnce:
			nextRuntime = nextRuntime + seconds

		if args is None:
			args = []
		if kwargs is None:
			kwargs = {}
		if not inspect.iscoroutinefunction(fn):
			logging.warning('Scheduler function %s is not a coroutine', fn)
			fn = asyncio.coroutine(fn)
		fn = functools.partial(fn, *args, **kwargs)
		return asyncio.ensure_future(self.scheduledTaskExecutor(fn, seconds, strictInterval, nextRuntime))

	async def scheduledTaskExecutor(self, fn, interval, strictInterval, nextRuntime):
		while True:
			ts = self.loop.time()
			if (ts >= nextRuntime):
				await fn()
				if strictInterval:
					while nextRuntime < ts:
						nextRuntime += interval
				else:
					nextRuntime = ts + interval
			await asyncio.sleep(nextRuntime - self.loop.time())

	def registerShutdown(self, fn):
		"""
		Register shutdown method. The method fn will be called the the server
		shuts down. Use this to clean up resources on shutdown.

		:param func fn: A function callback to call when the server shuts down
		"""
		if not inspect.iscoroutinefunction(fn):
			logging.warning('Shutdown function %s is not a coroutine', fn)
			fn = asyncio.coroutine(fn)
		self.shutdown.append(fn)

	async def eventLoop(self, startup):
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
		# Everything loaded. Wait for shutdown
		await self.shutdownEvent.wait()
		await asyncio.wait([fn() for fn in self.shutdown], timeout=120)
		asyncio.get_event_loop().stop()

	def run(self, startup=None):
		self.loop.create_task(self.eventLoop(startup))
		self.loop.run_forever()
		self.loop.close()
		return self.exitCode
		return sys.exit(self.exitCode)

	def queue(self, fn, *args, **kwargs):
		"""
		Queue a function to be executed later. All tasks in this queue will be
		run by the main thread. This is a thread safe function and can safely be
		used to syncronize with the main thread.
		The function myst be async. Currenly a warning will be thrown but this will be threated
		as an error in a future version.

		:returns: True if the task was queued
		:returns: False if the server is shutting down

		.. note::
			Calls to this method are threadsafe.
		"""
		if self.running == False:
			return False
		self.loop.call_soon_threadsafe(self.asyncQueue, fn, args, kwargs)
		return True

	def asyncQueue(self, fn, args, kwargs):
		"""Add a job from within the event loop.

		This method must be run in the event loop.
		"""
		if inspect.iscoroutinefunction(fn):
			#self.loop.create_task()  # From Python 3.7
			asyncio.ensure_future(fn(*args, **kwargs))
		elif hasattr(fn, '__callbackSafe__'):
			# Not coroutine, but safe to be called from main thread
			asyncio.ensure_future(asyncWrapper(fn, *args, **kwargs))
		else:
			logging.warning(
				'Function %s is not a coroutine, concider using createTask or wrap it in @callback instead',
				fn
			)
			syncWrapper = self.loop.run_in_executor(None, functools.partial(fn, *args, **kwargs))
			asyncio.ensure_future(syncWrapper)

	def quit(self, exitCode = 0):
		with self.lock:
			self.running = False
			self.exitCode = exitCode
		self.loop.call_soon_threadsafe(self.shutdownEvent.set)

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
		It is not recommended to call this method directly but instead use the signal decorator.
		Any extra parameters supplied will be forwarded to the slot.

		:param str msg: The signal name
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

from .SignalManager import SignalManager
