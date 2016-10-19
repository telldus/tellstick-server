# -*- coding: utf-8 -*-

from base import Application, implements, Plugin
from telldus import DeviceManager, Device, DeviceAbortException
from Protocol import Protocol
from Adapter import Adapter
from RF433Msg import RF433Msg
from tellduslive.base import TelldusLive, ITelldusLiveObserver
from board import Board
import logging

class RF433Node(Device):
	def __init__(self):
		super(RF433Node,self).__init__()
		self._nodeId = 0

	def localId(self):
		return self._nodeId

	def setId(self, newId):
		self._nodeId = newId
		super(RF433Node,self).setId(newId)

	def setNodeId(self, nodeId):
		self._nodeId = nodeId

	def typeString(self):
		return '433'

class SensorNode(RF433Node):
	def __init__(self):
		super(SensorNode,self).__init__()
		self._protocol = ''
		self._model = ''
		self._sensorId = 0

	def compare(self, protocol, model, sensorId):
		if self._protocol != protocol:
			return False
		if self._model != model:
			return False
		if self._sensorId != sensorId:
			return False
		return True

	def isDevice(self):
		return False

	def isSensor(self):
		return True

	def model(self):
		return self._model

	def params(self):
		return {
			'protocol': self._protocol,
			'model': self._model,
			'sensorId': self._sensorId,
			'type': 'sensor',
		}

	def protocol(self):
		return self._protocol

	def setParams(self, params):
		self._protocol = params.setdefault('protocol', '')
		self._model = params.setdefault('model', '')
		self._sensorId = params.setdefault('sensorId', 0)

	def updateValues(self, data):
		for value in data:
			self.setSensorValue(value['type'], value['value'], value['scale'])

class DeviceNode(RF433Node):
	def __init__(self, controller):
		super(DeviceNode,self).__init__()
		self.controller = controller
		self._protocol = ''
		self._model = ''
		self._protocolParams = {}

	def _command(self, action, value, success, failure, **kwargs):
		protocol = Protocol.protocolInstance(self._protocol)
		if not protocol:
			logging.warning("Unknown protocol %s", self._protocol)
			failure(0)
			return
		protocol.setModel(self._model)
		protocol.setParameters(self._protocolParams)
		msg = protocol.stringForMethod(action, value)
		if msg is None:
			failure(0)
			logging.error("Could not encode rf-data for %s:%s %s", self._protocol, self._model, action)
			return

		def s(params):
			success()
		def f():
			failure(Device.FAILED_STATUS_NO_REPLY)

		prefixes = {}
		if 'P' in msg:
			prefixes['P'] = msg['P']
		if 'R' in msg:
			prefixes['R'] = msg['R']
		if 'S' in msg:
			self.controller.queue(RF433Msg('S', msg['S'], prefixes, success=s, failure=f))

	def isDevice(self):
		return True

	def isSensor(self):
		return False

	def methods(self):
		protocol = Protocol.protocolInstance(self._protocol)
		if not protocol:
			return 0
		protocol.setModel(self._model)
		return protocol.methods()

	def params(self):
		return {
			'type': 'device',
			'protocol': self._protocol,
			'model': self._model,
			'protocolParams': self._protocolParams,
		}

	def setParams(self, params):
		self._protocol = params.setdefault('protocol', '')
		self._model = params.setdefault('model', '')
		self._protocolParams = params.setdefault('protocolParams', {})

class RF433(Plugin):
	implements(ITelldusLiveObserver)

	fwVersions = {
		'18F25K50': 1
	}

	def __init__(self):
		self.version = 0
		self.hwVersion = None
		self.devices = []
		self.sensors = []
		self.dev = Adapter(self, Board.rf433Port())
		deviceNode = DeviceNode(self.dev)
		self.deviceManager = DeviceManager(self.context)
		for d in self.deviceManager.retrieveDevices('433'):
			p = d.params()
			if 'type' not in p:
				continue
			if p['type'] == 'sensor':
				device = SensorNode()
				self.sensors.append(device)
			elif p['type'] == 'device':
				device = DeviceNode(self.dev)
				self.devices.append(device)
			else:
				continue
			device.setNodeId(d.id())
			device.setParams(p)
			self.deviceManager.addDevice(device)

		self.deviceManager.finishedLoading('433')
		self.dev.queue(RF433Msg('V', success=self.__version, failure=self.__noVersion))
		self.dev.queue(RF433Msg('H', success=self.__hwVersion, failure=self.__noHWVersion))
		self.live = TelldusLive(self.context)

	def addDevice(self, protocol, model, name, params):
		device = DeviceNode(self.dev)
		device.setName(name)
		device.setParams({
			'protocol': protocol,
			'model': model,
			'protocolParams': params
		})
		self.devices.append(device)
		self.deviceManager.addDevice(device)

	@TelldusLive.handler('rf433')
	def __handleCommand(self, msg):
		data = msg.argument(0).toNative()
		action = data['action']
		if action == 'addDevice':
			self.addDevice(data['protocol'], data['model'], data['name'], data['parameters'])

		elif action == 'deviceInfo':
			deviceId = data['device']
			for device in self.devices:
				if device.id() == deviceId:
					params = device.params()
					params['deviceId'] = deviceId
					self.live.pushToWeb('rf433', 'deviceInfo', params)
					return

		elif action == 'editDevice':
			deviceId = data['device']
			for device in self.devices:
				if device.id() == deviceId:
					device.setParams({
						'protocol': data['protocol'],
						'model': data['model'],
						'protocolParams': data['parameters']
					})
					device.paramUpdated('')
					break

		elif action == 'remove':
			deviceId = data['device']
			for device in self.devices:
				if device.id() == deviceId:
					self.deviceManager.removeDevice(deviceId)
					self.devices.remove(device)
					return

		else:
			logging.warning("Unknown rf433 command %s", action)

	def decode(self, msg):
		if 'class' in msg and msg['class'] == 'sensor':
			self.decodeSensor(msg)
			return
		Application.signal('rf433RawData', msg)
		msg = Protocol.decodeData(msg)
		for m in msg:
			self.decodeCommandData(m)

	def decodeCommandData(self, msg):
		protocol = msg['protocol']
		model = msg['model']
		method = msg['method']
		methods = Protocol.methodsForProtocol(protocol, model)
		if not method & methods:
			return
		for device in self.devices:
			params = device.params()
			if params['protocol'] != protocol:
				continue
			if not method & device.methods():
				continue
			deviceParams = params['protocolParams']
			thisDevice = True
			for parameter in Protocol.parametersForProtocol(protocol, model):
				if parameter not in msg:
					thisDevice = False
					break
				if parameter not in deviceParams:
					thisDevice = False
					break
				if msg[parameter] != deviceParams[parameter]:
					thisDevice = False
					break
			if thisDevice:
				device.setState(method, None)

	def decodeData(self, cmd, params):
		if cmd == 'W':
			self.decode(params)
		elif cmd == 'V':
			# New version received, probably after firmware upload
			self.__version(params)
		else:
			logging.debug("Unknown data: %s", str(cmd))

	def decodeSensor(self, msg):
		protocol = Protocol.protocolInstance(msg['protocol'])
		if not protocol:
			logging.error("No known protocol for %s", msg['protocol'])
			return
		data = protocol.decodeData(msg)
		if not data:
			return
		p = data['protocol']
		m = data['model']
		sensorId = data['id']
		sensorData = data['values']
		sensor = None
		for s in self.sensors:
			if s.compare(p, m, sensorId):
				sensor = s
				break
		if sensor is None:
			sensor = SensorNode()
			sensor.setParams({'protocol': p, 'model': m, 'sensorId': sensorId})
			self.sensors.append(sensor)
			self.deviceManager.addDevice(sensor)
		sensor.updateValues(sensorData)

	def __noVersion(self):
		logging.warning("Could not get firmware version for RF433, force upgrade")
		self.dev.updateFirmware()

	def __noHWVersion(self):
		logging.warning("Could not get hw version for RF433")

	def __hwVersion(self, version):
		logging.debug("Got HW version %s", version)
		self.hwVersion = version
		if version not in RF433.fwVersions:
			return
		fwVersion = RF433.fwVersions[self.hwVersion]
		if fwVersion != self.version:
			logging.info("Version %i is to old, update firmware", self.version)
			self.dev.updateFirmware()

	def __version(self, version):
		self.version = version
		logging.info("RF433 version: %i", self.version)
