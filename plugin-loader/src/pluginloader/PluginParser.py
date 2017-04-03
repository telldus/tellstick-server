# -*- coding: utf-8 -*-

from board import Board
import httplib
import xml.parsers.expat

class PluginParser(object):
	def parse(self):
		print "Update plugins"
		conn = httplib.HTTPConnection('fw.telldus.com:80')
		try:
			conn.request('GET', '/plugins.xml')
			response = conn.getresponse()
		except:
			logging.error("Could not get plugins list")
			return

		self.queue = []
		self.plugin = None
		self.edition = None
		self.plugins = []
		self.content = ''
		def startElement(name, attrs):
			self.queue.append((name, attrs))
			if name == 'plugin':
				self.plugin = {
					'author': '',
					'author-email': '',
					'name': str(attrs['name']),
					'category': str(attrs['category']),
					'compatible': False,
				}
				if 'color' in attrs:
					self.plugin['color'] = str(attrs['color'])
				return
			if self.plugin != None:
				if name == 'author':
					if 'name' in attrs:
						self.plugin['author'] = str(attrs['name'])
					if 'email' in attrs :
						self.plugin['author-email'] = str(attrs['email'])
				if name == 'edition':
					# TODO, check minimumSoftwareVersion and maximumSoftwareVersion
					self.edition = attrs
					return
				if self.edition != None:
					if name == 'file':
						self.edition['file'] = {
							'size': int(attrs['size']),
							'sha1': str(attrs['sha1']),
						}
		def characterDataHandler(c):
			self.content = self.content + c
		def endElement(name):
			(el, attrs) = self.queue.pop()
			content = str(self.content.strip())
			self.content = ''
			if el != name:
				raise Exception("Error parsing xml")
			if self.plugin != None:
				if name == 'description':
					self.plugin['description'] = content
				elif name == 'plugin':
					if self.plugin['compatible'] == True:
						del self.plugin['compatible']
						self.plugins.append(self.plugin)
					self.plugin = None
			if self.edition != None:
				if name == 'edition':
					self.plugin['file'] = self.edition['file']
					if 'icon' in self.edition:
						self.plugin['icon'] = self.edition['icon']
					self.plugin['version'] = str(self.edition['version'])
					self.edition = None
				elif name == 'file':
					self.edition['file']['url'] = content
				elif name == 'hardware':
					if content == Board.product():
						self.plugin['compatible'] = True
				elif name == 'icon':
					self.edition['icon'] = content
		
		p = xml.parsers.expat.ParserCreate()

		p.StartElementHandler = startElement
		p.EndElementHandler = endElement
		p.CharacterDataHandler = characterDataHandler
		p.Parse(response.read())
		return self.plugins
