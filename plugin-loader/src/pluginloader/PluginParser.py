# -*- coding: utf-8 -*-

import logging
import httplib
import xml.parsers.expat

from board import Board


class PluginParser(object):
	def __init__(self):
		self.queue = []
		self.plugin = None
		self.edition = None
		self.plugins = []
		self.content = ''

	def parse(self):
		conn = httplib.HTTPConnection('fw.telldus.com:80')
		try:
			conn.request('GET', '/plugins.xml')
			response = conn.getresponse()
		except Exception:
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
			if self.plugin is not None:
				if name == 'author':
					if 'name' in attrs:
						self.plugin['author'] = str(attrs['name'])
					if 'email' in attrs:
						self.plugin['author-email'] = str(attrs['email'])
				if name == 'edition':
					# TODO, check minimumSoftwareVersion and maximumSoftwareVersion
					self.edition = attrs
					return
				if self.edition is not None:
					if name == 'file':
						self.edition['file'] = {
						    'size': int(attrs['size']),
						    'sha1': str(attrs['sha1']),
						}

		def characterDataHandler(content):
			self.content = self.content + content

		def endElement(name):
			(element, attrs) = self.queue.pop()
			content = str(self.content.strip())
			self.content = ''
			if element != name:
				raise Exception("Error parsing xml")
			if self.plugin is not None:
				if name == 'description':
					self.plugin['description'] = content
				elif name == 'plugin':
					if self.plugin['compatible']:
						del self.plugin['compatible']
						self.plugins.append(self.plugin)
					self.plugin = None
			if self.edition is not None:
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

		parser = xml.parsers.expat.ParserCreate()

		parser.StartElementHandler = startElement
		parser.EndElementHandler = endElement
		parser.CharacterDataHandler = characterDataHandler
		parser.Parse(response.read())
		return self.plugins
