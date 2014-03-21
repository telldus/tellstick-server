import cherrypy, threading
from base import Application, IInterface, ObserverCollection, Plugin
from genshi.template import TemplateLoader, loader
from pkg_resources import resource_filename

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

	def handle(self, *paths, **params):
		menu = []
		templates = []
		for o in self.observers:
			arr = o.getMenuItems()
			if type(arr) == list:
				menu.extend(arr)
		for o in self.observers:
			if o.matchRequest(paths):
				template, data = o.handleRequest(paths, params)
				break
		tmpl = self.loadTemplate(template)
		data['menu'] = menu
		stream = tmpl.generate(title='TellStick ZNet', **data)
		return stream.render('html', doctype='html')

	def __call__(self, *args, **kwargs):
		return self.handle(*args, **kwargs)
RequestHandler.exposed = True
