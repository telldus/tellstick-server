import cherrypy, mimetypes, threading
from base import Application, IInterface, ObserverCollection, Plugin
from genshi.template import TemplateLoader, loader
from pkg_resources import resource_filename, resource_exists, resource_stream

class IWebRequestHandler(IInterface):
	"""Interface defenition for handling web requests"""
	def handleRequest(paths, params):
		"""Handle a request. Return a tuple with template and data"""
	def getMenuItems():
		"""Return array with menu items"""
	def getTemplatesDirs():
		""" Location of templates provided by plugin. """
	def matchRequest(path):
		"""Return true if we handle this request"""

class Server(Plugin):
	def __init__(self):
		super(Server,self).__init__()
		mimetypes.init()
		cherrypy.config.update({
			'server.socket_host': '0.0.0.0'
		})
		cherrypy.tree.mount(RequestHandler(self.context))
		cherrypy.engine.autoreload.unsubscribe()
		cherrypy.engine.start()
		Application().registerShutdown(self.stop)

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
		if plugin != '' and resource_exists(plugin, 'htdocs/' + path):
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
		for o in self.observers:
			if o.matchRequest(path):
				template, data = o.handleRequest(path, params)
				break
		if template is None:
			raise cherrypy.NotFound()
		tmpl = self.loadTemplate(template)
		data['menu'] = menu
		stream = tmpl.generate(title='TellStick ZNet', **data)
		return stream.render('html', doctype='html')

	def __call__(self, plugin = '', *args, **kwargs):
		path = [x for x in args]
		return self.handle(plugin, path, **kwargs)
RequestHandler.exposed = True
