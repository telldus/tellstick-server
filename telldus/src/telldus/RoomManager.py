# -*- coding: utf-8 -*-

from base import \
	ISignalObserver, \
	Plugin, \
	Settings, \
	implements, \
	signal
from tellduslive.base import TelldusLive, LiveMessage, ITelldusLiveObserver

__name__ = 'telldus'  # pylint: disable=W0622

class RoomManager(Plugin):
	"""The roommanager holds and manages all the rooms in the server"""
	implements(ISignalObserver)
	implements(ITelldusLiveObserver)
	public = True

	def __init__(self):
		self.rooms = {}
		self.settings = Settings('telldus.rooms')
		self.rooms = self.settings.get('rooms', {})

	@TelldusLive.handler('room')
	def __handleRoom(self, msg):
		data = msg.argument(0).toNative()
		if 'name' in data:
			if isinstance(data['name'], int):
				data['name'] = str(data['name'])
			else:
				data['name'] = data['name'].decode('UTF-8')
		live = TelldusLive(self.context)
		if data['action'] == 'set':
			oldResponsible = ''
			if data['id'] in self.rooms:
				oldResponsible = self.rooms[data['id']]['responsible']
			self.rooms[data['id']] = {
				'name': data.get('name', ''),
				'parent': data.get('parent', ''),
				'color': data.get('color', ''),
				'content': data.get('content', ''),
				'icon': data.get('icon', ''),
				'responsible': data['responsible'],
				'mode': '',
			}
			if self.live.registered and (data['responsible'] == self.live.uuid or oldResponsible  == self.live.uuid):
				msg = LiveMessage('RoomSet')
				msg.append({'id': data['id']})
				msg.append(self.rooms[data['id']])
				live.send(msg)
			self.settings['rooms'] = self.rooms
			return

		if data['action'] == 'remove':
			room = self.rooms.pop(data['id'], None)
			if room is None:
				return
			if live.registered and room['responsible'] == self.live.uuid:
				msg = LiveMessage('RoomRemoved')
				msg.append({'id': data['id']})
				live.send(msg)
			self.settings['rooms'] = self.rooms
			return
