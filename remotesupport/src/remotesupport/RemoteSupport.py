# -*- coding: utf-8 -*-

from base import Plugin, implements
from tellduslive.base import TelldusLive, ITelldusLiveObserver
from pkg_resources import resource_filename
import paramiko, select, socket, threading
import logging

class RemoteSupport(Plugin):
	implements(ITelldusLiveObserver)

	@TelldusLive.handler('remotesupport')
	def __handleCommand(self, msg):
		data = msg.argument(0).toNative()
		if data['action'] == 'start':
			self.start(data['server'], data['username'])

	def start(self, server, username):
		client = paramiko.SSHClient()
		client.load_system_host_keys()
		client.set_missing_host_key_policy(paramiko.WarningPolicy())
		try:
			client.connect(server, 22, username=username, key_filename=resource_filename('remotesupport', 'id_rsa'))
		except Exception as e:
			logging.exception(e)
			return
		transport = client.get_transport()
		port = transport.request_port_forward('', 0)
		TelldusLive(self.context).pushToWeb('remotesupport', 'connected', port)
		thr = threading.Thread(target=self.waitForConnection, args=(client,transport,))
		thr.setDaemon(True)
		thr.start()

	def waitForConnection(self, client, transport):
		chan = transport.accept(60)
		if chan is None:
			transport.close()
			TelldusLive(self.context).pushToWeb('remotesupport', 'disconnected', None)
			return
		thr = threading.Thread(target=self.tunnelhandler, args=(client, chan,))
		thr.setDaemon(True)
		thr.start()

	def tunnelhandler(self, client, chan):
		sock = socket.socket()
		try:
			sock.connect(('localhost', 22))
		except Exception as e:
			logging.exception(e)
			return

		while True:
			r, w, x = select.select([sock, chan], [], [], 3)
			if sock in r:
				data = sock.recv(1024)
				if len(data) == 0:
					break
				chan.send(data)
			if chan in r:
				data = chan.recv(1024)
				if len(data) == 0:
					break
				sock.send(data)
		chan.close()
		sock.close()
		TelldusLive(self.context).pushToWeb('remotesupport', 'disconnected', None)
		client.close()
		client = None
