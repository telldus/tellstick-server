# -*- coding: utf-8 -*-

import httplib
import fcntl, socket, struct
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
		conn = httplib.HTTPConnection("api.telldus.com:80")
		conn.request('GET', "/server/assign?protocolVersion=2&mac=%s" % ServerList.getMacAddr('eth0'))
		response = conn.getresponse()

		p = xml.parsers.expat.ParserCreate()

		p.StartElementHandler = self._startElement
		p.Parse(response.read())

	def _startElement(self, name, attrs):
		if (name == 'server'):
			self.list.append(attrs)

	@staticmethod
	def getMacAddr(ifname):
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		info = fcntl.ioctl(s.fileno(), 0x8927,  struct.pack('256s', ifname[:15]))
		return ''.join(['%02X' % ord(char) for char in info[18:24]])
