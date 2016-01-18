# -*- coding: utf-8 -*-

from base import Application, Plugin, ISignalObserver, implements, slot
from board import Board
from web.base import IWebRequestHandler
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pkg_resources import resource_filename
from LuaScript import LuaScript
import glob, os
import logging, cherrypy

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
	implements(ISignalObserver)

	def __init__(self):
		self.scripts = []
		self.load()
		self.fileobserver = Observer()
		self.fileobserver.schedule(FileChangedHandler(self), Board.luaScriptPath())
		self.fileobserver.start()
		Application().registerShutdown(self.shutdown)

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

	def getTemplatesDirs(self):
		return [resource_filename('lua', 'templates')]

	def matchRequest(self, plugin, path):
		if plugin != 'lua':
			return False
		if path in ['', 'delete', 'new', 'save']:
			return True
		return False

	def handleRequest(self, plugin, path, params, **kwargs):
		script = None
		if path == 'save':
			if 'script' not in cherrypy.request.body.params or 'code' not in cherrypy.request.body.params:
				return 'empty.html', {}
			self.saveScript(cherrypy.request.body.params['script'], cherrypy.request.body.params['code'])
			return 'empty.html', {}
		elif path == 'new':
			okChars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-'
			if 'name' not in params:
				return 'empty.html', {}
			name = ''.join([c for c in params['name'] if c in okChars])
			if len(name) == 0:
				return 'empty.html', {}
			with open('%s/%s.lua' % (Board.luaScriptPath(), name), 'w') as f:
				f.write('-- Empty file')
			return 'empty.html', {}
		elif path == 'delete':
			if 'name' not in params:
				return 'empty.html', {}
			for s in self.scripts:
				if s.name == params['name']:
					os.remove(s.filename)
					break
			return 'empty.html', {}
		elif 'edit' in params:
			for s in self.scripts:
				if s.name == params['edit']:
					script = s
					break
		return 'lua.html', {'scripts': self.scripts, 'script': script}

	def load(self):
		for f in glob.glob('%s/*.lua' % Board.luaScriptPath()):
			self.scripts.append(LuaScript(f, self.context))
		for s in self.scripts:
			s.load()

	def requireAuthentication(self, plugin, path):
		return plugin != 'lua'

	def saveScript(self, scriptName, code):
		for script in self.scripts:
			if script.name != scriptName:
				continue
			with open(script.filename, 'w') as f:
				f.write(code)
			# overlayfs does not support inofify for filechanges so we need to signal manually
			script.reload()
			break

	@slot()
	def slot(self, message, *args, **kwargs):
		name = 'on%s%s' % (message[0].upper(), message[1:])
		for script in self.scripts:
			script.call(name, *args)

	def shutdown(self):
		self.fileobserver.stop()
		self.fileobserver.join()
		for script in self.scripts:
			script.shutdown()
