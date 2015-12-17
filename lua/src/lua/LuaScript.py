# -*- coding: utf-8 -*-

from base import Application
from telldus import DeviceManager
from web.base import Server
from lupa import LuaRuntime, lua_type
from threading import Thread, Condition, Lock
import os, types

# Whitelist functions known to be safe.
safeFunctions = {
	'_VERSION': [],
	'assert': [],
	'coroutine': ['create', 'resume', 'running', 'status', 'wrap', 'yield'],
	'error': [],
	'ipairs': [],
	'math': ['abs', 'acos', 'asin', 'atan', 'atan2', 'ceil', 'cos', 'cosh', 'deg', 'exp', 'floor', 'fmod', 'frexp', 'huge', 'ldexp', 'log', 'log10', 'max', 'min', 'modf', 'pi', 'pow', 'rad', 'random', 'randomseed', 'sin', 'sinh', 'sqrt', 'tan', 'tanh'],
	'next': [],
	'os': ['clock', 'date', 'difftime', 'time'],
	'pairs': [],
	'pcall': [],
	'print': [],
	'select': [],
	'string': ['byte', 'char', 'find', 'format', 'gmatch', 'gsub', 'len', 'lower', 'match', 'rep', 'reverse', 'sub', 'upper'],
	'table': ['concat', 'insert', 'maxn', 'remove', 'sort'],
	'tonumber': [],
	'tostring': [],
	'type': [],
	'unpack': [],
	'xpcall': []
}

class LuaScript(object):
	CLOSED, LOADING, RUNNING, IDLE, ERROR, CLOSING = range(6)

	def __init__(self, filename, context):
		self.filename = filename
		self.name = os.path.basename(filename)
		self.context = context
		self.__queue = []
		self.__thread = Thread(target=self.__run, name=self.name)
		self.__threadLock = Condition(Lock())
		self.__state = LuaScript.CLOSED
		self.__stateLock = Lock()
		self.__thread.start()

	def call(self, name, *args):
		if self.state() not in [LuaScript.RUNNING, LuaScript.IDLE]:
			return
		if name not in self.lua.globals():
			return
		self.__threadLock.acquire()
		try:
			self.__queue.append((name, args))
			self.__threadLock.notifyAll()
		finally:
			self.__threadLock.release()

	def load(self):
		self.reload()

	def p(self, msg, *args):
		try:
			logMsg = msg % args
		except:
			logMsg = msg
		Server(self.context).webSocketSend('lua', 'log', logMsg)

	def reload(self):
		with open(self.filename, 'r') as f:
			self.code = f.read()
		self.__setState(LuaScript.LOADING)
		self.__notifyThread()

	def shutdown(self):
		self.__setState(LuaScript.CLOSING)
		self.__notifyThread()
		self.__thread.join()
		self.p("Script %s unloaded", self.name)

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
					pass
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
				fn = getattr(self.lua.globals(), name)
				try:
					self.__setState(LuaScript.RUNNING)
					fn(*args)
				except Exception as e:
					self.p("Could not execute function %s: %s", name, e)
				self.__setState(LuaScript.IDLE)

	def __load(self):
		self.lua = LuaRuntime(
			unpack_returned_tuples=True,
			register_eval=False,
			attribute_handlers=(self.__getter,self.__setter)
		)
		setattr(self.lua.globals(), 'print', self.p)
		# Remove potentially dangerous functions
		self.__sandboxInterpreter()
		self.lua.globals().deviceManager = DeviceManager(self.context)
		try:
			self.__setState(LuaScript.RUNNING)
			self.lua.execute(self.code)
			self.__setState(LuaScript.IDLE)
			self.p("Script %s loaded", self.name)
		except Exception as e:
			self.__setState(LuaScript.ERROR)
			self.p("Could not execute lua script %s", e)

	def __sandboxInterpreter(self):
		for obj in self.lua.globals():
			if obj == '_G':
				# Allow _G here to not start recursion
				continue
			if obj not in safeFunctions:
				del self.lua.globals()[obj]
				continue
			if lua_type(self.lua.globals()[obj]) != 'table':
				continue
			funcs = safeFunctions[obj]
			for func in self.lua.globals()[obj]:
				if func not in funcs:
					del self.lua.globals()[obj][func]

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
		if not hasattr(obj, attrName):
			raise AttributeError('object has no attribute "%s"' % attrName)
		attribute = getattr(obj, attrName)
		if type(attribute) in [int, str, unicode, float, types.NoneType]:
			# Allow primitive attributes directly
			return attribute
		if type(attribute) == types.MethodType:
			# Get the unbound method to support obj:method() calling convention in Lua
			attribute = getattr(obj.__class__, attrName)
		elif type(attribute) != types.FunctionType:
			raise AttributeError('type "%s" is not allowed in Lua code' % type(attribute))
		condition = Condition()
		retval = []
		def mainThreadCaller(args, kwargs):
			# This is called from the main thread. Do the actual call here
			try:
				retval.append(attribute(*args, **kwargs))
			except:
				pass
			condition.acquire()
			try:
				condition.notifyAll()
			finally:
				condition.release()

		def proxyMethod(*args, **kwargs):
			# We are in the script thread here, we must syncronize with the main
			# thread before calling the attribute
			condition.acquire()
			try:
				Application().queue(mainThreadCaller, args, kwargs)
				condition.wait(20)  # Timeout to not let the script hang forever
				if len(retval):
					return retval.pop()
			finally:
				condition.release()
			raise AttributeError('The call to the function "%s" timed out' % attrName)
		return proxyMethod

	def __setter(self, obj, attrName, value):
		# Set it in the main thread
		Application().queue(setattr, obj, attrName, value)
