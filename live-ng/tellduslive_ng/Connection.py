# -*- coding: utf-8 -*-

import threading
import logging
from base import Settings
from board import Board
from sleekxmpp import ClientXMPP
from sleekxmpp.exceptions import IqError, IqTimeout

__name__ = 'tellduslive-ng'  # pylint: disable=W0622

class Connection(object):
	def __init__(self):
		settings = Settings('tellduslive.config')
		uuid = settings['uuid']
		self.xmpp = ClientXMPP(
			'%s@gateway.telldus.com' % uuid,
			'%s:%s' % (Board.getMacAddr(), Board.secret())
		)
		self.xmpp.add_event_handler("session_start", self.sessionStart)
		self.xmpp.add_event_handler("register", self.register)
		self.xmpp.register_plugin('xep_0030') # Service Discovery
		self.xmpp.register_plugin('xep_0077') # In-band registration
		self.shuttingDown = False
		# Connect is blocking. Do this in a separate thread
		threading.Thread(target=self.__start, name='XMPP connector').start()

	def register(self, form):
		del form  # Unused
		resp = self.xmpp.Iq()
		resp['type'] = 'set'
		resp['register']['username'] = self.xmpp.boundjid.user
		resp['register']['password'] = self.xmpp.password
		try:
			resp.send(now=True)
			return
		except IqError as error:
			code = error.iq['error']['code']
			if code == '409':  # Already exists, this is ok
				return
		except IqTimeout:
			logging.warning("IQ timeout")
		logging.warning("Could not register, disconnect!")
		self.shutdown()

	def sessionStart(self, event):
		del event
		self.xmpp.send_presence()
		self.xmpp.get_roster()

	def shutdown(self):
		self.shuttingDown = True
		self.xmpp.disconnect()

	def __start(self):
		self.xmpp.connect()
		self.xmpp.process(block=False)
		if self.shuttingDown:
			self.xmpp.disconnect()

