import cherrypy, json, mimetypes, threading
from ws4py.server.cherrypyserver import WebSocketPlugin, WebSocketTool
from ws4py.websocket import WebSocket
from ws4py.messaging import TextMessage
from base import Application, IInterface, ObserverCollection, Plugin
from genshi.template import TemplateLoader, loader
from pkg_resources import resource_filename, resource_exists, resource_stream, resource_isdir
import logging

class IWebRequestHandler(IInterface):
	"""Interface defenition for handling web requests"""
	def handleRequest(plugin, paths, params):
		"""Handle a request. Return a tuple with template and data"""
	def getMenuItems():
		"""Return array with menu items"""
	def getTemplatesDirs():
		""" Location of templates provided by plugin. """
	def matchRequest(plugin, path):
		"""Return true if we handle this request"""

class WebRequest(object):
	def __init__(self, request):
		self.__request = request

	def base(self):
		return self.__request.base

class WebSocketHandler(WebSocket):
	pass

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

	def loadTemplate(self, filename):
		if not self.templates:
			dirs = [resource_filename('web', 'templates')]
			for o in self.observers:
				d = o.getTemplatesDirs()
				if type(d) == list:
					dirs.extend(d)
			self.templates = TemplateLoader(dirs)
		return self.templates.load(filename)

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
		response = None
		for o in self.observers:
			if o.matchRequest(plugin, path):
				response = o.handleRequest(plugin, path, params, request=WebRequest(cherrypy.request))
				break
		if response is None:
			raise cherrypy.NotFound()
		if isinstance(response, WebResponseRedirect):
			if response.url[:4] == 'http':
				raise cherrypy.HTTPRedirect(response.url)
			raise cherrypy.HTTPRedirect('%s%s%s' % (plugin, '' if response.url[0] == '/' else '/', response.url))
		template, data = response
		if template is None:
			raise cherrypy.NotFound()
		tmpl = self.loadTemplate(template)
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
