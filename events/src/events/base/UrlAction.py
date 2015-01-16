# -*- coding: utf-8 -*-

from Action import Action
from threading import Thread
import base64, httplib, urlparse

class UrlAction(Action):
	def __init__(self, **kwargs):
		super(UrlAction,self).__init__(**kwargs)
		self.url = ''

	def parseParam(self, name, value):
		if name == 'url':
			self.url = str(value)

	def execute(self):
		# Invoke in a new thread to not block
		thread = Thread(target=self.__execute, name='UrlAction')
		thread.start()

	def __execute(self):
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

		conn = httplib.HTTPConnection('%s:%i' % (sendHost, port))
		conn.request('GET', sendPath)
		response = conn.getresponse()
