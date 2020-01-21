import json
import logging
import mimetypes
import os
import cherrypy
from ws4py.server.cherrypyserver import WebSocketPlugin, WebSocketTool
from ws4py.websocket import WebSocket
from base import Application, implements, IInterface, ObserverCollection, Plugin
from genshi.template import TemplateLoader
from pkg_resources import resource_filename, resource_exists, resource_stream, resource_isdir

# pylint: disable=E0213,E0211
class IWebRequestHandler(IInterface):
	"""Interface definition for handling web requests"""
	def handleRequest(plugin, paths, params, request):
		"""Handle a request. Return a tuple with template and data"""
	def getMenuItems():
		"""Return array with menu items"""
	def getNoSessionPaths():
		"""Return array with paths that should be excluded from session management"""
	def getTemplatesDirs():
		""" Location of templates provided by plugin. """
	def matchRequest(plugin, path):
		"""Return true if we handle this request"""
	def requireAuthentication(plugin, path):
		"""
		Checks if a request require the user to log in first. Return False if the resource should
		be available to anyone.
		"""

class IWebRequestAuthenticationHandler(IInterface):
	"""Interface definition for authenticating web requests"""
	def isUrlAuthorized(request):
		"""Check if url is authorized"""
	def handleAuthenticationForUrl(request):
		"""Handle authentication for a given request"""
	def loginProvider():
		"""Return info about this login provider"""

class WebRequest(object):
	def __init__(self, request):
		self.__request = request

	def base(self):
		return self.__request.base

	def loggedIn(self):
		raise cherrypy.HTTPRedirect(self.session('returnTo', '/'))

	def header(self, param):
		return self.__request.headers.get(param, None)

	def method(self):
		return self.__request.method

	def params(self):
		return self.__request.body.params

	def post(self, param, default=None):
		return self.__request.body.params.get(param, default)

	@staticmethod
	def session(key, default=None):
		return cherrypy.session.get(key, default)

	@staticmethod
	def setSession(key, value):
		cherrypy.session[key] = value

class WebSocketHandler(WebSocket):
	pass

class WebResponse(object):
	def __init__(self, statusCode=200):
		self.statusCode = statusCode
		self.data = ''

	def output(self, response):
		pass

class WebResponseHtml(WebResponse):
	def __init__(self, filename, statusCode=200):
		super(WebResponseHtml, self).__init__(statusCode)
		self.filename = filename

	def setDirs(self, __plugin, dirs):
		if not isinstance(dirs, list):
			dirs = []
		dirs.append(resource_filename('web', 'templates'))
		for directory in dirs:
			path = os.path.join(directory, self.filename)
			if os.path.exists(path):
				with open(path) as fd:
					self.data = fd.read()
				return

class WebResponseJson(WebResponse):
	def __init__(self, data, pretty=True, statusCode=200):
		super(WebResponseJson, self).__init__(statusCode)
		if pretty:
			self.data = json.dumps(data, sort_keys=True, indent=2, separators=(',', ': ')).encode('utf-8')
		else:
			self.data = json.dumps(data).encode('utf-8')

	def output(self, response):
		response.headers['Content-Type'] = 'application/json; charset=utf-8'

class WebResponseLocalFile(WebResponse):
	def __init__(self, path):
		super(WebResponseLocalFile, self).__init__()
		self.data = open(path, 'r')
		self.contentType, __encoding = mimetypes.guess_type(path, strict=False)

	def output(self, response):
		response.headers['Content-Type'] = self.contentType

class WebResponseRedirect(object):
	def __init__(self, url):
		self.url = url

class Server(Plugin):
	def __init__(self):
		super(Server, self).__init__()
		mimetypes.init()
		port = 80 if os.getuid() == 0 else 8080
		cherrypy.config.update({
			'server.socket_host': '::',
			'server.socket_port': port,
			'tools.sessions.on': True,
			'tools.sessions.timeout': 60,
			'tools.sessions.httponly': True,
		})
		reqHandler = RequestHandler(self.context, self)
		self.mainApp = cherrypy.tree.mount(reqHandler, '', config={
			'/ws': {
				'tools.websocket.on': True,
				'tools.websocket.handler_cls': WebSocketHandler
			}
		})
		cherrypy.engine.autoreload.unsubscribe()
		WebSocketPlugin(cherrypy.engine).subscribe()
		cherrypy.tools.websocket = WebSocketTool()
		cherrypy.engine.start()
		Application().registerShutdown(self.stop)
		reqHandler.setSessionPaths()

	@staticmethod
	def webSocketSend(module, action, data):
		cherrypy.engine.publish('websocket-broadcast', json.dumps({
			'module': module,
			'action': action,
			'data': data,
		}))

	@staticmethod
	def stop():
		cherrypy.engine.exit()

class RequestHandler(object):
	observers = ObserverCollection(IWebRequestHandler)

	def __init__(self, context, server):
		self.templates = None
		self.context = context
		self.server = server

	@staticmethod
	def loadTemplate(filename, dirs):
		if not isinstance(dirs, list):
			dirs = []
		dirs.append(resource_filename('web', 'templates'))
		templates = TemplateLoader(dirs)
		return templates.load(filename)

	def handle(self, plugin, path, **params):
		path = '/'.join(path)
		# First check for the file in htdocs
		try:
			if plugin != '' and \
			   resource_exists(plugin, 'htdocs/' + path) and \
			   resource_isdir(plugin, 'htdocs/' + path) is False:
				mimetype, __encoding = mimetypes.guess_type(path, strict=False)
				if mimetype is not None:
					cherrypy.response.headers['Content-Type'] = mimetype
				return resource_stream(plugin, 'htdocs/' + path)
		except Exception as __error:
			pass
		menu = []
		for observer in self.observers:
			arr = observer.getMenuItems()
			if isinstance(arr, list):
				menu.extend(arr)
		template = None
		templateDirs = []
		response = None
		request = WebRequest(cherrypy.request)
		for observer in self.observers:
			if not observer.matchRequest(plugin, path):
				continue
			requireAuth = observer.requireAuthentication(plugin, path)
			if requireAuth != False:
				WebRequestHandler(self.context).isUrlAuthorized(request)
			response = observer.handleRequest(plugin, path, params, request=request)
			templateDirs = observer.getTemplatesDirs()
			break
		if response is None:
			raise cherrypy.NotFound()
		if isinstance(response, WebResponseRedirect):
			if response.url[:4] == 'http':
				raise cherrypy.HTTPRedirect(response.url)
			raise cherrypy.HTTPRedirect('/%s%s%s' % (
				plugin,
				'' if response.url[0] == '/' else '/',
				response.url
			))
		elif isinstance(response, WebResponse):
			if isinstance(response, WebResponseHtml):
				response.setDirs(plugin, templateDirs)
			cherrypy.response.status = response.statusCode
			response.output(cherrypy.response)
			return response.data
		template, data = response
		if template is None:
			raise cherrypy.NotFound()
		tmpl = self.loadTemplate(template, templateDirs)
		data['menu'] = menu
		stream = tmpl.generate(title='TellStick ZNet', **data)
		return stream.render('html', doctype='html')

	def setSessionPaths(self):
		noSessionPaths = []
		for observer in self.observers:
			noSessionPath = observer.getNoSessionPaths()
			if isinstance(noSessionPath, list):
				noSessionPaths.extend(noSessionPath)
			for nsPath in noSessionPaths:
				self.server.mainApp.merge({nsPath: {
					'tools.sessions.on': False,
				}})

	def __call__(self, plugin='', *args, **kwargs):
		if plugin == 'ws':
			# Ignore, this is for websocket
			return
		path = [x for x in args]
		return self.handle(plugin, path, **kwargs)
RequestHandler.exposed = True

class WebRequestHandler(Plugin):
	"""Default handler for the /web subpath"""

	authObservers = ObserverCollection(IWebRequestAuthenticationHandler)
	implements(IWebRequestHandler)

	@staticmethod
	def getTemplatesDirs():
		return [resource_filename('web', 'templates')]

	def handleRequest(self, plugin, path, __params, **__kwargs):
		if plugin != 'web':
			return None
		if path == 'authFailed':
			return 'authFailed.html', {}
		if path == 'login':
			providers = []
			for observer in self.authObservers:
				provider = observer.loginProvider()
				if provider is not None:
					providers.append(provider)
			if len(providers) == 1:
				# Only one provider. Use it
				raise cherrypy.HTTPRedirect(providers[0]['url'])
			return 'login.html', {'providers': providers}
		return None

	def isUrlAuthorized(self, request):
		if len(self.authObservers) == 0:
			raise cherrypy.HTTPRedirect('/web/authFailed?reason=noAuthHandlersConfigured')
		for observer in self.authObservers:
			ret = observer.isUrlAuthorized(request)
			if ret is True:
				return True
		request.setSession('returnTo', '%s?%s' % (
			cherrypy.request.path_info,
			cherrypy.request.query_string
		))
		raise cherrypy.HTTPRedirect('/web/login')

	@staticmethod
	def matchRequest(plugin, path):
		if plugin != 'web':
			return False
		if path in ['authFailed', 'login']:
			return True
		return False

	@staticmethod
	def requireAuthentication(plugin, __path):
		return plugin != 'web'
