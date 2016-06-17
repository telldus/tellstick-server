# -*- coding: utf-8 -*-

from base import Plugin, implements
from board import Board
from web.base import IWebRequestHandler
import glob
#import gnupg
import logging
import pkg_resources
import traceback

class Loader(Plugin):
	def __init__(self):
		self.loadPlugins()

	def loadPlugins(self):
		for f in glob.glob('%s/*.egg' % Board.pluginPath()):
			self.verifyAndLoadPlugin(f)

	def printBacktrace(self, bt):
		for f in bt:
			logging.error(str(f))

	def verifyAndLoadPlugin(self, path):
		if not self.verifyPlugin(path):
			return
		self.__loadPlugin(path)

	def verifyPlugin(self, path):
		# Check signature
		# TODO
		#gpg = gnupg.GPG(keyring='telldus-plugins.gpg')
		#v = gpg.verify_file(open(path), '%s.asc' % path)
		#if v.valid is not True:
		#	raise Exception('Could not verify signature: %s' % v.status)
		return True

	def __loadPlugin(self, path):
		for dist in pkg_resources.find_distributions(path):
			logging.warning("Loading plugin %s %s", dist.project_name, dist.version)
			dist.activate()
			for entry in dist.get_entry_map(group='telldus.plugins'):
				info = dist.get_entry_info('telldus.startup', entry)
				try:
					info.load()
				except Exception as e:
					exc_type, exc_value, exc_traceback = sys.exc_info()
					logging.error("Could not load %s", str(entry))
					logging.error(str(e))
					self.printBacktrace(traceback.extract_tb(exc_traceback))

			for entry in dist.get_entry_map(group='telldus.startup'):
				info = dist.get_entry_info('telldus.startup', entry)
				try:
					moduleClass = info.load()
					if issubclass(moduleClass, Plugin):
						m = moduleClass(self.context)
					else:
						m = moduleClass()
				except Exception as e:
					exc_type, exc_value, exc_traceback = sys.exc_info()
					logging.error("Could not load %s", str(entry))
					logging.error(str(e))
					self.printBacktrace(traceback.extract_tb(exc_traceback))

class WebFrontend(Plugin):
	implements(IWebRequestHandler)

	def getTemplatesDirs(self):
		return [pkg_resources.resource_filename('pluginloader', 'templates')]

	def matchRequest(self, plugin, path):
		if plugin != 'pluginloader':
			return False
		if path in ['']:
			return True
		return False

	def handleRequest(self, plugin, path, params, request, **kwargs):
		if request.method() == 'POST' and 'pluginfile' in params:
			# TODO: Verify the file upload and extract signature from egg
			f = params['pluginfile']
			with open('%s/%s' % (Board.pluginPath(), f.filename), 'w') as wf:
				wf.write(f.file.read())
		return 'pluginloader.html', {}
