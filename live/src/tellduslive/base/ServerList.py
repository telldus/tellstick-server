# -*- coding: utf-8 -*-

import httplib
import xml.parsers.expat

class ServerList():

	def __init__(self):
		self.list = []

	def popServer(self):
		if (self.list == []):
			try:
				self.retrieveServerList()
			except Exception as e:
				print "Could not retrieve server list:", e
				return False

		if (self.list == []):
			return False

		return self.list.pop(0)


	def retrieveServerList(self):
		#conn = httplib.HTTPConnection("api.telldus.com:80")
		conn = httplib.HTTPConnection("api.telldus.net:80")
		conn.request('GET', "/server/assign?protocolVersion=2")
		response = conn.getresponse()

		p = xml.parsers.expat.ParserCreate()

		p.StartElementHandler = self._startElement
		p.Parse(response.read())

	def _startElement(self, name, attrs):
		if (name == 'server'):
			self.list.append(attrs)
