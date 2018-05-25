# -*- coding: utf-8 -*-

import glob
import os

import cherrypy
from api import IApiCallHandler, apicall
from base import Application, Plugin, SignalManager, ISignalObserver, implements, slot
from board import Board
from web.base import IWebRequestHandler, WebResponseJson
from telldus.web import IWebReactHandler
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from lua.LuaScript import LuaScript

class FileChangedHandler(FileSystemEventHandler):
	def __init__(self, parent):
		self.parent = parent

	def on_created(self, event):
		if event.is_directory:
			return
		self.parent.fileCreated(event.src_path)

	def on_deleted(self, event):
		if event.is_directory:
			return
		self.parent.fileRemoved(event.src_path)

class Lua(Plugin):
	implements(IWebRequestHandler)
	implements(IWebReactHandler)
	implements(ISignalObserver)
	implements(IApiCallHandler)

	def __init__(self):
		self.scripts = []
		self.load()
		self.fileobserver = Observer()
		self.fileobserver.schedule(FileChangedHandler(self), Board.luaScriptPath())
		self.fileobserver.start()
		Application().registerShutdown(self.shutdown)

	@apicall('lua', 'call')
	def apiCallFunction(self, script, function, **kwargs):
		"""
		Calls a lua function in a script. Required methods:
		  script: The name of the script. With or witout the .lua extension.
		  function: The name of the function to call.

		Any extra parameters will be sent to the function as a lua table as the
		first parameter.
		"""
		if not script.endswith('.lua'):
			script = '%s.lua' % script
		for scriptObj in self.scripts:
			if scriptObj.name != script:
				continue
			if not scriptObj.call(function, kwargs):
				raise Exception('Script %s does not define function "%s"' % (script, function))
			return True
		raise Exception('Script %s not found' % script)

	def fileCreated(self, filename):
		if not filename.endswith('.lua'):
			return
		for script in self.scripts:
			if script.filename == filename:
				# Already loaded
				return
		script = LuaScript(filename, self.context)
		self.scripts.append(script)
		script.load()

	def fileRemoved(self, filename):
		for i, script in enumerate(self.scripts):
			if script.filename == filename:
				script.shutdown()
				del self.scripts[i]
				break

	@staticmethod
	def getReactComponents():
		return {
			'lua': {
				'title': 'Lua scripts (beta)',
				'script': 'lua/lua.js',
				'tags': ['menu'],
			}
		}

	@staticmethod
	def matchRequest(plugin, path):
		if plugin != 'lua':
			return False
		if path in ['delete', 'new', 'save', 'script', 'scripts', 'signals']:
			return True
		return False

	def handleRequest(self, plugin, path, params, **__kwargs):
		del plugin
		script = None
		if path == 'save':
			if 'script' not in cherrypy.request.body.params or 'code' not in cherrypy.request.body.params:
				return WebResponseJson({'error': 'Malformed request, parameter script or code missing'})
			self.saveScript(cherrypy.request.body.params['script'], cherrypy.request.body.params['code'])
			return WebResponseJson({'success': True})
		elif path == 'new':
			okChars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-'
			if 'name' not in params:
				return WebResponseJson({'error': 'Invalid script name'})
			name = ''.join([c for c in params['name'] if c in okChars])
			if len(name) == 0:
				return WebResponseJson({'error': 'Invalid script name'})
			filename = '%s/%s.lua' % (Board.luaScriptPath(), name)
			with open(filename, 'w') as fd:
				fd.write('-- File: %s.lua\n\nfunction onInit()\n\tprint("Hello world")\nend' % name)
			self.fileCreated(filename)
			return WebResponseJson({'success': True, 'name': '%s.lua' % name})
		elif path == 'delete':
			if 'name' not in params:
				return WebResponseJson({'error': 'Invalid script name'})
			for script in self.scripts:
				if script.name == params['name']:
					os.remove(script.filename)
					self.fileRemoved(script.filename)
					break
			return WebResponseJson({'success': True})
		elif path == 'script':
			for script in self.scripts:
				if script.name == params['name']:
					return WebResponseJson({
						'name': params['name'],
						'code': script.code,
					})
			return WebResponseJson({})
		elif path == 'scripts':
			return WebResponseJson([{
				'name': script.name
			} for script in sorted(self.scripts, key=lambda s: s.name.lower())])
		elif path == 'signals':
			return WebResponseJson(self.signals())
		elif 'edit' in params:
			for s in self.scripts:
				if s.name == params['edit']:
					script = s
					break
		return None

	def load(self):
		for filename in glob.glob('%s/*.lua' % Board.luaScriptPath()):
			self.scripts.append(LuaScript(filename, self.context))
		for script in self.scripts:
			script.load()

	def saveScript(self, scriptName, code):
		for script in self.scripts:
			if script.name != scriptName:
				continue
			with open(script.filename, 'w') as fd:
				fd.write(code)
			# overlayfs does not support inofify for filechanges so we need to signal manually
			script.reload()
			break

	@staticmethod
	def signals():
		signals = [{
			'name': 'on%s%s' % (x[0].upper(), x[1:]),
			'doc': SignalManager.signals[x].doc(),
			'args': SignalManager.signals[x].args(),
		} for x in SignalManager.signals]
		signals.append({
			'name': 'onInit',
			'doc': 'Called when the script is loaded',
			'args': [],
		})
		return signals

	@slot()
	def onSignals(self, message, *args, **__kwargs):
		name = 'on%s%s' % (message[0].upper(), message[1:])
		for script in self.scripts:
			script.call(name, *args)

	def shutdown(self):
		self.fileobserver.stop()
		self.fileobserver.join()
		for script in self.scripts:
			script.shutdown()
