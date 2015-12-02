# -*- coding: utf-8 -*-

from telldus import DeviceManager
from web.base import Server
from lupa import LuaRuntime
import os

class LuaScript(object):
	CLOSED, LOADING, LOADED, RUNNING, ERROR = range(5)

	def __init__(self, filename, context):
		self.filename = filename
		self.name = os.path.basename(filename)
		self.status = LuaScript.CLOSED
		self.context = context

	def call(self, name, *args):
		if name not in self.lua.globals():
			return
		fn = getattr(self.lua.globals(), name)
		try:
			fn(*args)
		except Exception as e:
			self.p("Could not execute function %s: %s", name, e)

	def load(self):
		self.reload()

	def p(self, msg, *args):
		try:
			logMsg = msg % args
		except:
			logMsg = msg
		Server(self.context).webSocketSend('lua', 'log', logMsg)

	def reload(self):
		self.status = LuaScript.LOADING
		with open(self.filename, 'r') as f:
			self.code = f.read()
		self.lua = LuaRuntime(
			unpack_returned_tuples=True,
			register_eval=False,
			attribute_filter=self.__filterAttributeAccess
		)
		setattr(self.lua.globals(), 'print', self.p)
		# Remove dangerous functions
		del self.lua.globals().os['exit']
		self.lua.globals().deviceManager = DeviceManager(self.context)
		try:
			self.lua.execute(self.code)
			self.status = LuaScript.LOADED
			self.p("Script %s loaded", self.name)
		except Exception as e:
			self.status = LuaScript.ERROR
			self.p("Could not execute lua script %s", e)

	def unload(self):
		self.p("Script %s unloaded", self.name)

	def __filterAttributeAccess(self, obj, attrName, isSetting):
		#logging.info("Try to access %s, %s, %s", obj, attrName, isSetting)
		return attrName
