# -*- coding: utf-8 -*-

import logging
import os
from threading import Thread, Condition, Lock, Timer
import types
import weakref

from base import Application
from web.base import Server
from lupa import LuaRuntime, lua_type

# Whitelist functions known to be safe.
SAFE_FUNCTIONS = {
	'_VERSION': [],
	'assert': [],
	'coroutine': ['create', 'resume', 'running', 'status', 'wrap', 'yield'],
	'error': [],
	'ipairs': [],
	'math': [
		'abs', 'acos', 'asin', 'atan', 'atan2', 'ceil', 'cos', 'cosh', 'deg', 'exp', 'floor',
		'fmod', 'frexp', 'huge', 'ldexp', 'log', 'log10', 'max', 'min', 'modf', 'pi', 'pow',
		'rad', 'random', 'randomseed', 'sin', 'sinh', 'sqrt', 'tan', 'tanh'
	],
	'next': [],
	'os': ['clock', 'date', 'difftime', 'time'],
	'pairs': [],
	'pcall': [],
	'print': [],
	'python': ['as_attrgetter', 'as_itemgetter', 'as_function', 'enumerate', 'iter', 'iterex'],
	'select': [],
	'string': [
		'byte', 'char', 'find', 'format', 'gmatch', 'gsub', 'len', 'lower', 'match', 'rep',
		'reverse', 'sub', 'upper'
	],
	'table': ['concat', 'insert', 'maxn', 'remove', 'sort'],
	'tonumber': [],
	'tostring': [],
	'type': [],
	'unpack': [],
	'xpcall': []
}

class List(object):
	"""
	This object is available in Lua code as the object :class:`list` and is
	a helper class for working with Python lists.
	"""
	len = len
	@staticmethod
	def new(*args):
		"""Create a new Python list for use with Python code.

		Example:
		local pythonList = list.new(1, 2, 3, 4)
		"""
		return list(args)

	@staticmethod
	def slice(collection, start=None, end=None, step=None):
		"""Retrieve the start, stop and step indices from the slice object `list`.
		Treats indices greater than length as errors.

		This can be used for slicing python lists (e.g. l[0:10:2])."""
		return collection[slice(start, end, step)]

#pylint: disable=W0613
def sleep(milliseconds):
	"""
	Delay for a specified amount of time.

	  :milliseconds: The number of milliseconds to sleep.

	"""
	pass
	# The real function is not implemented here. This is just for documentation.

class LuaThread(object):
	def __init__(self):
		pass

	def abort(self):
		pass

class SleepingLuaThread(LuaThread):
	def __init__(self, ms):
		super(SleepingLuaThread, self).__init__()
		self.milliseconds = ms
		self.timer = None

	def abort(self):
		if self.timer:
			self.timer.cancel()

	def start(self, callback):
		self.timer = Timer(self.milliseconds/1000.0, callback)
		self.timer.start()

class LuaFunctionWrapper(object):
	def __init__(self, script, cb):
		self.script = script
		self.callback = cb
		self.destructionHandlers = []

	def __del__(self):
		self.script.gcReferences()
		self.callback = None
		self.script = None

	def __call__(self, *args):
		if self.callback is None:
			return
		self.script.callFunc(self.callback, *args)
		self.callback = None

	def abort(self):
		self.script = None
		self.callback = None
		for callback, args, kwargs in self.destructionHandlers:
			Application().queue(callback, *args, **kwargs)
		self.destructionHandlers[:] = []

	def registerDestructionHandler(self, callback, *args, **kwargs):
		self.destructionHandlers.append((callback, args, kwargs,))

class PythonObjectWrapper(object):
	"""
	On some platforms python segfaults then we return the python plugin
	from the require function.
	This dummy wrapper object seems to solve this issue. Feel free to remove
	when the actual issue is resolved.
	"""
	def __init__(self, obj):
		self.obj = obj

	def __getitem__(self, item):
		"""This function seems to be key for the segfaults to not occur"""
		pass

	def __getattr__(self, attr):
		method = getattr(self.obj, attr)
		if not callable(method):
			return method
		def func(__self, *args, **kwargs):
			return method(*args, **kwargs)
		return func

	def __repr__(self):
		return repr(self.obj)

class LuaScript(object):
	CLOSED, LOADING, RUNNING, IDLE, ERROR, CLOSING = range(6)

	def __init__(self, filename, context):
		self.code = ''
		self.filename = filename
		self.lua = None
		self.name = os.path.basename(filename)
		self.context = context
		self.runningLuaThread = None
		self.runningLuaThreads = []
		self.references = []
		self.__allowedSignals = []
		self.__queue = []
		self.__thread = Thread(target=self.__run, name=self.name)
		self.__threadLock = Condition(Lock())
		self.__state = LuaScript.CLOSED
		self.__stateLock = Lock()
		self.__thread.start()

	def call(self, name, *args):
		if self.state() not in [LuaScript.RUNNING, LuaScript.IDLE]:
			return False
		if name not in self.__allowedSignals:
			return False
		self.__threadLock.acquire()
		try:
			self.__queue.append((name, args))
			self.__threadLock.notifyAll()
		finally:
			self.__threadLock.release()
		return True

	def callFunc(self, func, *args):
		if self.state() not in [LuaScript.RUNNING, LuaScript.IDLE]:
			return
		self.__threadLock.acquire()
		try:
			self.__queue.append((func, args))
			self.__threadLock.notifyAll()
		finally:
			self.__threadLock.release()

	def gcReferences(self):
		self.references[:] = [r for r in self.references if r() is not None]

	def load(self):
		self.reload()

	def log(self, msg, *args):
		try:
			logMsg = msg % args
		except Exception as __error:
			logMsg = msg
		Server(self.context).webSocketSend('lua', 'log', logMsg)

	def reload(self):
		with open(self.filename, 'r') as fd:
			self.code = fd.read()
		self.__setState(LuaScript.LOADING)
		self.__notifyThread()

	def shutdown(self):
		self.__setState(LuaScript.CLOSING)
		self.__notifyThread()
		self.__thread.join()
		self.log("Script %s unloaded", self.name)

	def state(self):
		with self.__stateLock:
			return self.__state

	def __notifyThread(self):
		self.__threadLock.acquire()
		try:
			self.__threadLock.notifyAll()
		finally:
			self.__threadLock.release()

	def __run(self):
		while True:
			state = self.state()
			self.__threadLock.acquire()
			task = None
			try:
				if len(self.__queue):
					task = self.__queue.pop(0)
				elif state in [LuaScript.LOADING, LuaScript.CLOSING]:
					# Abort any threads that might be running
					for thread in self.runningLuaThreads:
						thread.abort()
					self.runningLuaThreads = []
					for ref in self.references:
						if ref() is not None:
							ref().abort()
					self.references[:] = []
				else:
					self.__threadLock.wait(300)
			finally:
				self.__threadLock.release()
			if state == LuaScript.CLOSING:
				self.__setState(LuaScript.CLOSED)
				return
			if state == LuaScript.LOADING:
				self.__load()
			elif task is not None:
				name, args = task
				args = list(args)
				for i, arg in enumerate(args):
					if type(arg) == dict:
						args[i] = self.lua.table_from(arg)
				if isinstance(name, (str, unicode)):
					func = getattr(self.lua.globals(), name)
					self.runningLuaThread = func.coroutine(*args)
				elif lua_type(name) == 'thread':
					self.runningLuaThread = name
				elif lua_type(name) == 'function':
					self.runningLuaThread = name.coroutine(*args)
				else:
					continue
				try:
					self.__setState(LuaScript.RUNNING)
					self.runningLuaThread.send(None)
				except StopIteration:
					pass
				except Exception as error:
					self.log("Could not execute function %s: %s", name, error)
				self.runningLuaThread = None
				self.__setState(LuaScript.IDLE)

	def __load(self):
		self.lua = LuaRuntime(
			unpack_returned_tuples=True,
			register_eval=False,
			attribute_handlers=(self.__getter, self.__setter)
		)
		setattr(self.lua.globals(), 'print', self.log)
		# Remove potentially dangerous functions
		self.__sandboxInterpreter()
		# Install a sleep function as lua script since it need to be able to yield
		self.lua.execute('function sleep(ms)\nif suspend(ms) then\ncoroutine.yield()\nend\nend')
		setattr(self.lua.globals(), 'suspend', self.__luaSleep)
		try:
			self.lua.execute(self.code)
			# Register which signals the script accepts so we don't need to access
			# the interpreter from any other thread. That leads to locks.
			self.__allowedSignals = []
			for func in self.lua.globals():
				self.__allowedSignals.append(func)
			self.__setState(LuaScript.IDLE)
			# Allow script to initialize itself
			self.call('onInit')
			self.log("Script %s loaded", self.name)
		except Exception as error:
			self.__setState(LuaScript.ERROR)
			self.log("Could not load lua script %s: %s", self.name, error)

	def __luaSleep(self, milliseconds):
		if self.state() != LuaScript.RUNNING:
			self.log("sleep() cannot be called while the script is loading")
			return False
		coroutine = self.runningLuaThread
		thread = SleepingLuaThread(milliseconds)
		def resume():
			if thread in self.runningLuaThreads:
				self.runningLuaThreads.remove(thread)
			if not bool(coroutine):
				# Cannot call coroutine anymore
				return
			self.__threadLock.acquire()
			try:
				self.__queue.append((coroutine, []))
				self.__threadLock.notifyAll()
			finally:
				self.__threadLock.release()
		thread.start(resume)
		self.runningLuaThreads.append(thread)
		return True

	def __require(self, plugin):
		obj = self.context.request(plugin)
		if obj is None:
			self.log("Plugin %s not found. Available plugins:", plugin)
			for key in self.context.pluginsList():
				self.log(key)
		return PythonObjectWrapper(obj) if obj is not None else None

	def __sandboxInterpreter(self):
		for obj in self.lua.globals():
			if obj == '_G':
				# Allow _G here to not start recursion
				continue
			if obj not in SAFE_FUNCTIONS:
				del self.lua.globals()[obj]
				continue
			if lua_type(self.lua.globals()[obj]) != 'table':
				continue
			funcs = SAFE_FUNCTIONS[obj]
			for func in self.lua.globals()[obj]:
				if func not in funcs:
					del self.lua.globals()[obj][func]
		self.lua.globals().list = List
		self.lua.globals().require = self.__require

	def __setState(self, newState):
		with self.__stateLock:
			self.__state = newState

	def __getter(self, obj, attrName):
		# Our getter method is a bit special. Since the lua scripts are executed in
		# it's own thread we cannot call any python code directly. We cannot simply
		# queue it to the main thread either since we must support returning any
		# return value from the functions. The concept here is that attributes are
		# returned directly but any access to functions returns a proxy method
		# instead. A call to the proxy method send a call to the main thread, blocks
		# and then wait for it to be executed.
		if isinstance(attrName, int):
			# obj is probably a list
			attribute = obj[attrName]
		elif not hasattr(obj, attrName):
			raise AttributeError('object has no attribute "%s"' % attrName)
		else:
			attribute = getattr(obj, attrName)
		if isinstance(attribute, (int, str, unicode, float, types.NoneType)):
			# Allow primitive attributes directly
			return attribute
		if isinstance(attribute, types.MethodType):
			# Get the unbound method to support obj:method() calling convention in Lua
			attribute = getattr(obj.__class__, attrName)
		elif not isinstance(attribute, (types.FunctionType, types.BuiltinFunctionType)):
			raise AttributeError(
				'type "%s" is not allowed in Lua code. Trying to access attribute %s in object %s' %
				(type(attribute), attrName, obj)
			)
		condition = Condition()
		retval = {}
		def mainThreadCaller(args, kwargs):
			# This is called from the main thread. Do the actual call here
			try:
				retval['return'] = attribute(*args, **kwargs)
			except Exception as error:
				retval['error'] = str(error)
			condition.acquire()
			try:
				condition.notifyAll()
			finally:
				condition.release()

		def proxyMethod(*args, **kwargs):
			# We are in the script thread here, we must syncronize with the main
			# thread before calling the attribute
			condition.acquire()
			args = list(args)
			if len(args) >= 2 and lua_type(args[1]) == 'table':
				# First parameter is a lua table. Handle this as **kwargs call
				kwargs = self.__wrapArgument(args[1])
				del args[1]
			for i, __arg in enumerate(args):
				args[i] = self.__wrapArgument(args[i])
			try:
				Application().queue(mainThreadCaller, args, kwargs)
				condition.wait(20)  # Timeout to not let the script hang forever
				if 'error' in retval:
					self.log("Error during call: %s", retval['error'])
					raise AttributeError(retval['error'])
				elif 'return' in retval:
					if isinstance(retval['return'], dict):
						# Wrap to lua table
						return self.lua.table_from(retval['return'])
					return retval['return']
			finally:
				condition.release()
			raise AttributeError('The call to the function "%s" timed out' % attrName)
		return proxyMethod

	@staticmethod
	def __setter(obj, attrName, value):
		# Set it in the main thread
		Application().queue(setattr, obj, attrName, value)

	def __wrapArgument(self, arg):
		if lua_type(arg) == 'function':
			func = LuaFunctionWrapper(self, arg)
			self.references.append(weakref.ref(func))
			return func
		elif lua_type(arg) == 'table':
			table = dict(arg)
			for key in table:
				# Recursive wrap
				table[key] = self.__wrapArgument(table[key])
			return table
		return arg
