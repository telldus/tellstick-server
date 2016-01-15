import cherrypy, json, mimetypes, threading
from ws4py.server.cherrypyserver import WebSocketPlugin, WebSocketTool
from ws4py.websocket import WebSocket
from ws4py.messaging import TextMessage
from base import Application, implements, IInterface, ObserverCollection, Plugin
from genshi.template import TemplateLoader, loader
from pkg_resources import resource_filename, resource_exists, resource_stream, resource_isdir
import logging

class IWebRequestHandler(IInterface):
	"""Interface definition for handling web requests"""
	def handleRequest(plugin, paths, params, request):
		"""Handle a request. Return a tuple with template and data"""
	def getMenuItems():
		"""Return array with menu items"""
	def getTemplatesDirs():
		""" Location of templates provided by plugin. """
	def matchRequest(plugin, path):
		"""Return true if we handle this request"""
	def requireAuthentication(plugin, path):
		"""Checks if a request require the user to log in first. Return False if the resource should be available to anyone."""

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

	def header(self, param):
		return self.__request.headers.get(param, None)

	def method(self):
		return self.__request.method

	def post(self, param, default=None):
		return self.__request.body.params.get(param, default)

class WebSocketHandler(WebSocket):
	pass

class WebResponse(object):
	def __init__(self, statusCode = 200):
		self.statusCode = statusCode
		self.data = ''

	def output(self, response):
		pass

class WebResponseJson(WebResponse):
	def __init__(self, data, pretty=True, statusCode = 200):
		super(WebResponseJson,self).__init__(statusCode)
		if pretty:
			self.data = json.dumps(data, sort_keys=True, indent=2, separators=(',', ': '))
		else:
			self.data = json.dumps(data)

	def output(self, response):
		response.headers['Content-Type'] = 'Content-Type: application/json; charset=utf-8'

class WebResponseRedirect(object):
	def __init__(self, url):
		self.url = url

class Server(Plugin):
	def __init__(self):
		super(Server,self).__init__()
		mimetypes.init()
		cherrypy.config.update({
			'server.socket_host': '::',
			'server.socket_port': 80,
		})
		cherrypy.tree.mount(RequestHandler(self.context), '', config = {
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

	def webSocketSend(self, module, action, data):
		cherrypy.engine.publish('websocket-broadcast', json.dumps({
			'module': module,
			'action': action,
			'data': data,
		}))

	def stop(self):
		cherrypy.engine.exit()

class RequestHandler(object):
	observers = ObserverCollection(IWebRequestHandler)

	def __init__(self, context):
		self.templates = None
		self.context = context

	def loadTemplate(self, filename, dirs):
		if type(dirs) is not list:
			dirs = []
		dirs.append(resource_filename('web', 'templates'))
		templates = TemplateLoader(dirs)
		return templates.load(filename)

	def handle(self, plugin, p, **params):
		path = '/'.join(p)
		# First check for the file in htdocs
		if plugin != '' and resource_exists(plugin, 'htdocs/' + path) and resource_isdir(plugin, 'htdocs/' + path) is False:
			mimetype, encoding = mimetypes.guess_type(path, strict=False)
			if mimetype is not None:
				cherrypy.response.headers['Content-Type'] = mimetype
			return resource_stream(plugin, 'htdocs/' + path)

		menu = []
		templates = []
		for o in self.observers:
			arr = o.getMenuItems()
			if type(arr) == list:
				menu.extend(arr)
		template = None
		templateDirs = []
		response = None
		request = WebRequest(cherrypy.request)
		for o in self.observers:
			if not o.matchRequest(plugin, path):
				continue
			requireAuth = o.requireAuthentication(plugin, path)
			if requireAuth != False:
				ret = WebRequestHandler(self.context).isUrlAuthorized(request)
			response = o.handleRequest(plugin, path, params, request=request)
			templateDirs = o.getTemplatesDirs()
			break
		if response is None:
			raise cherrypy.NotFound()
		if isinstance(response, WebResponseRedirect):
			if response.url[:4] == 'http':
				raise cherrypy.HTTPRedirect(response.url)
			raise cherrypy.HTTPRedirect('%s%s%s' % (plugin, '' if response.url[0] == '/' else '/', response.url))
		elif isinstance(response, WebResponse):
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

	def __call__(self, plugin = '', *args, **kwargs):
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

	def getTemplatesDirs(self):
		return [resource_filename('web', 'templates')]

	def handleRequest(self, plugin, path, params, request):
		if plugin != 'web':
			return None
		if path == 'authFailed':
			return 'authFailed.html', {}
		if path == 'login':
			providers = []
			for o in self.authObservers:
				provider = o.loginProvider()
				if provider is not None:
					providers.append(provider)
			return 'login.html', {'providers': providers}
		return None

	def isUrlAuthorized(self, request):
		if len(self.authObservers) == 0:
			raise cherrypy.HTTPRedirect('/web/authFailed?reason=noAuthHandlersConfigured')
		for o in self.authObservers:
			ret = o.isUrlAuthorized(request)
			if ret is True:
				return True
		raise cherrypy.HTTPRedirect('/web/login')

	def matchRequest(self, plugin, path):
		if plugin != 'web':
			return False
		if path in ['authFailed', 'login']:
			return True
		return False

	def requireAuthentication(self, plugin, path):
		return plugin != 'web'
