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
		self.roomlistEmpty = self.settings.get('roomlistEmpty', False)

	def getResponsibleRooms(self, responsible=None):
		if not responsible:
			live = TelldusLive(self.context)
			responsible = live.uuid
		rooms = {}
		for roomUUID in self.rooms:
			room = self.rooms[roomUUID]
			if room['responsible'] == responsible:
				rooms[roomUUID] = room
		return rooms

	def liveRegistered(self, msg, refreshRequired):
		if refreshRequired:
			self.syncRoom()

	def reportRooms(self, rooms, removedRooms = None):
		report = {}
		if not rooms and not self.roomlistEmpty and not removedRooms:
			# only allow empty room reports if we know it has been
			# explicitly emptied
			return
		if rooms or self.roomlistEmpty:
			report['rooms'] = rooms
		if removedRooms:
			report['removedRooms'] = removedRooms
		msg = LiveMessage('RoomReport')
		msg.append(report)
		TelldusLive(self.context).send(msg)

	def roomChanged(self, room1, room2):
		for prop in room1:
			if not room1[prop] == room2[prop]:
				return True
		return False

	def setMode(self, roomId, mode, setAlways = 1):
		"""
		Set a room to a new mode
		"""
		room = self.rooms.get(roomId, None)
		if not room:
			return
		setAlways = int(setAlways)
		if setAlways or room['mode'] != mode:
			if room['mode'] != mode:
				room['mode'] = mode
				self.settings['rooms'] = self.rooms
			live = TelldusLive(self.context)
			if live.registered and room.get('responsible', '') == live.uuid:
				# Notify live if we are the owner
				msg = LiveMessage('RoomModeSet')
				msg.append({
					'id': roomId,
					'mode': mode
				})
				live.send(msg)
			self.__modeChanged(roomId, mode, 'room', room.get('name', ''))

	def syncRoom(self):
		TelldusLive(self.context).send(LiveMessage("roomsync-request"))

	@signal('modeChanged')
	def __modeChanged(self, objectId, modeId, objectType, objectName):
		"""
		Called every time the mode changes for a room
		"""
		pass

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
				# existing room
				room = self.rooms[data['id']]
				oldResponsible = room['responsible']
				validKeys = ['name', 'color', 'content', 'icon', 'responsible']
				for key in validKeys:
					if key in data:
						room[key] = data.get(key, '')
				if 'mode' in data and room['mode'] != data.get('mode', ''):
					room['mode'] = data.get('mode', '')
					self.__modeChanged(data['id'], room['mode'], 'room', room['name'])
				self.rooms[data['id']] = room
			else:
				# new room
				self.rooms[data['id']] = {
					'name': data.get('name', ''),
					'parent': data.get('parent', ''),
					'color': data.get('color', ''),
					'content': data.get('content', ''),
					'icon': data.get('icon', ''),
					'responsible': data['responsible'],
					'mode': data.get('mode', ''),
				}
			if live.registered and \
			    (data['responsible'] == live.uuid or oldResponsible == live.uuid):
				room = self.rooms[data['id']]
				msg = LiveMessage('RoomSet')
				msg.append({
					# No need to call get() on room here since we know every value has at least a
					# default value above
					'id': data['id'],
					'name': room['name'],
					'parent': room['parent'],
					'color': room['color'],
					'content': room['content'],
					'icon': room['icon'],
					'responsible': room['responsible'],
					'mode': room['mode'],
				})
				live.send(msg)
			self.settings['rooms'] = self.rooms
			return

		if data['action'] == 'remove':
			room = self.rooms.pop(data['id'], None)
			if room is None:
				return
			if live.registered and room['responsible'] == live.uuid:
				msg = LiveMessage('RoomRemoved')
				msg.append({'id': data['id']})
				live.send(msg)
			if len(self.getResponsibleRooms()) == 0:
				self.settings['roomlistEmpty'] = True
				self.roomlistEmpty = True

			self.settings['rooms'] = self.rooms
			return

		if data['action'] == 'setMode':
			self.setMode(data.get('id', None), data.get('mode', ''), data.get('setAlways', 1))
			return

		if data['action'] == 'sync':
			rooms = data['rooms']
			responsibleRooms = self.getResponsibleRooms()
			if not rooms and responsibleRooms:
				# list from server was completely empty but we have rooms locally,
				# this might be an error in the fetching, or we have added rooms locally
				# when offline. In any case, don't sync this time, just post our rooms
				# for next time
				self.reportRooms(responsibleRooms)
				return
			changedRooms = {}
			newRooms = {}
			removedRooms = []
			for roomUUID in rooms:
				room = rooms[roomUUID]
				if room['responsible'] == live.uuid:
					# we are responsible for this room
					if roomUUID not in self.rooms:
						# this room does not exist locally anymore
						removedRooms.append(roomUUID)
						continue
					localRoom = self.rooms[roomUUID]
					if self.roomChanged(room, localRoom):
						changedRooms[roomUUID] = localRoom
				else:
					newRooms[roomUUID] = room

			newRooms.update(responsibleRooms)
			self.rooms = newRooms
			self.reportRooms(changedRooms, removedRooms)
			self.settings['rooms'] = self.rooms
