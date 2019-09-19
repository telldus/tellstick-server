# -*- coding: utf-8 -*-

import base64
import http.client
from threading import Thread
import urllib.parse

from .Action import Action

class UrlAction(Action):
	def __init__(self, **kwargs):
		super(UrlAction, self).__init__(**kwargs)
		self.url = ''
		self.port = 80

	def parseParam(self, name, value):
		if name == 'url':
			if isinstance(value, unicode):
				value = value.encode('utf-8')
			self.url = str(value)

	def execute(self, triggerInfo=None):
		triggerInfo = triggerInfo or {}
		# Invoke in a new thread to not block
		thread = Thread(target=self.__execute, name='UrlAction')
		thread.start()

	def __execute(self):
		headers = {}
		url = urlparse.urlparse(self.url)
		sendHost = url.netloc  #clean url
		port = 80  # default 80
		if url.port != '' and url.port != None:
			self.port = int(url.port)

		sendPath = url.path
		if sendPath == '':
			sendPath = '/'
		if url.query != '':
			sendPath = "%s?%s" % (sendPath, url.query)
		atIndex = sendHost.find('@')
		if atIndex >= 0:
			headers['Authorization'] = 'Basic %s' % (base64.b64encode(sendHost[:atIndex]))
			sendHost = sendHost[atIndex+1:]

		if url.scheme=="http":
			conn = httplib.HTTPConnection('%s' % (sendHost))
		else:
			conn = httplib.HTTPSConnection('%s' % (sendHost))
		conn.request('GET', sendPath, None, headers)
		conn.getresponse()
