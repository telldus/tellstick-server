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
import traceback
from typing import Any, Callable
import signal
import sys
from .Plugin import Plugin, PluginContext

async def asyncWrapper(func, *args, **kwargs):
	return func(*args, **kwargs)

class mainthread():  # pylint: disable=C0103
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

class Application():
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
			cls._instance = super(Application, cls).__new__(cls)
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
		self.loop.call_soon_threadsafe(
			functools.partial(self.asyncCreateTask, cbFn, *args, **kwargs)
		)

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
			return asyncio.ensure_future(cbFn(*args, **kwargs))
		# Not compatible with asyncio. May be blocking. Run in own thread.
		syncWrapper = self.loop.run_in_executor(None, functools.partial(cbFn, *args, **kwargs))
		return asyncio.ensure_future(syncWrapper)

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
		if not inspect.iscoroutinefunction(func):
			logging.warning('Scheduler function %s is not a coroutine', func)
			func = asyncio.coroutine(func)
		func = functools.partial(func, *args, **kwargs)
		return asyncio.ensure_future(
			self.scheduledTaskExecutor(func, seconds, strictInterval, nextRuntime)
		)

	async def scheduledTaskExecutor(self, func, interval, strictInterval, nextRuntime):
		while True:
			timestamp = self.loop.time()
			if (timestamp >= nextRuntime):
				await func()
				if strictInterval:
					while nextRuntime < timestamp:
						nextRuntime += interval
				else:
					nextRuntime = timestamp + interval
			await asyncio.sleep(nextRuntime - self.loop.time())

	def registerShutdown(self, func):
		"""
		Register shutdown method. The method func will be called the the server
		shuts down. Use this to clean up resources on shutdown.

		:param func func: A function callback to call when the server shuts down
		"""
		if not inspect.iscoroutinefunction(func):
			logging.warning('Shutdown function %s is not a coroutine', func)
			func = asyncio.coroutine(func)
		self.shutdown.append(func)

	async def eventLoop(self, startup):
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
		# Everything loaded. Wait for shutdown
		await self.shutdownEvent.wait()
		await asyncio.wait([fn() for fn in self.shutdown], timeout=120)
		asyncio.get_event_loop().stop()

	def run(self, startup=None):
		self.loop.create_task(self.eventLoop(startup))
		self.loop.run_forever()
		self.loop.close()
		return sys.exit(self.exitCode)

	def queue(self, func, *args, **kwargs):
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
		if not self.running:
			return False
		self.loop.call_soon_threadsafe(self.asyncQueue, func, args, kwargs)
		return True

	def asyncQueue(self, func, args, kwargs):
		"""Add a job from within the event loop.

		This method must be run in the event loop.
		"""
		if inspect.iscoroutinefunction(func):
			#self.loop.create_task()  # From Python 3.7
			asyncio.ensure_future(func(*args, **kwargs))
		elif hasattr(func, '__callbackSafe__'):
			# Not coroutine, but safe to be called from main thread
			asyncio.ensure_future(asyncWrapper(func, *args, **kwargs))
		else:
			logging.warning(
				'Function %s is not a coroutine, concider using createTask or wrap it in @callback instead',
				func
			)
			syncWrapper = self.loop.run_in_executor(None, functools.partial(func, *args, **kwargs))
			asyncio.ensure_future(syncWrapper)

	def quit(self, exitCode=0):
		with self.lock:
			self.running = False
			self.exitCode = exitCode
		self.loop.call_soon_threadsafe(self.shutdownEvent.set)

	@staticmethod
	def printBacktrace(backtrace):
		for frame in backtrace:
			logging.getLogger(__name__).error(str(frame))

	@staticmethod
	def printException(exception):
		__exc_type, __exc_value, exc_traceback = sys.exc_info()
		logging.getLogger(__name__).error(str(exception))
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

	def __signal(self, signum, __frame):
		logging.getLogger(__name__).info("Signal %d caught", signum)
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

from .SignalManager import SignalManager  # pylint: disable=C0413
