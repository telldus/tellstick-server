# -*- coding: utf-8 -*-

import logging
import time
from threading import Timer
from uuid import UUID

from base import (
    Application, implements, ISignalObserver, Plugin, signal, slot
)
from board import Board
from telldus import DeviceManager, Device
from tellduslive.base import TelldusLive, ITelldusLiveObserver

from .Protocol import Protocol
from .Adapter import Adapter
from .RF433Msg import RF433Msg

_LOGGER = logging.getLogger(__name__)


class RF433Node(Device):
	def __init__(self):
		super(RF433Node, self).__init__()
		self._nodeId = 0

	def localId(self):
		return self._nodeId

	def setId(self, newId):
		self._nodeId = newId
		super(RF433Node, self).setId(newId)

	def setNodeId(self, nodeId):
		self._nodeId = nodeId

	@staticmethod
	def typeString():
		return '433'

class SensorNode(RF433Node):
	def __init__(self):
		super(SensorNode, self).__init__()
		self._protocol = ''
		self._model = ''
		self._sensorId = 0
		self._packageCount = 0
		self.batteryLevel = None
		self.declaredDead = False

	def battery(self):
		return self.batteryLevel

	def compare(self, protocol, model, sensorId):
		if self._protocol != protocol:
			return False
		if self._model != model:
			return False
		if self._sensorId != sensorId:
			return False
		return True

	@staticmethod
	def isDevice():
		return False

	@staticmethod
	def isSensor():
		return True

	def isValid(self):
		if self._name and self._name != "Device " + str(self.localId()) and not self._ignored:
			return True  # name is set and not ignored, don't clean up automatically
		if not self._sensorValues:
			if not self.declaredDead:
				self.declaredDead = time.time()
				return True  # no sensor values, let the sensor exist for a week before deleting
			if self.declaredDead < (time.time() - 604800):
				return False  # Sensor has existed for a week, with no new incoming values. Delete.
			return True

		for valueType in self._sensorValues:
			for sensorType in self._sensorValues[valueType]:
				if sensorType['lastUpdated'] > (time.time() - 604800):
					# at least some value was updated during the last week
					return True
		return False

	def model(self):
		return self._model

	def name(self):
		# empty name for new 433-sensors (becomes "No name" in Telldus Live!)
		if self._name is not None and self._name != 'Device ' + str(self.localId()):
			return self._name
		return ''

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
		if self._packageCount == 6:
			if self._manager:
				# add to manager only now, that equals no live updates before this,
				# and no storage to file
				self._manager.addDevice(self)
			self._packageCount = self._packageCount + 1
		if self._packageCount < 6:
			self._packageCount = self._packageCount + 1
			return  # don't update any values yet
		if self.declaredDead:
			self.declaredDead = False
		self.setSensorValues(data)

class DeviceNode(RF433Node):
	def __init__(self, controller):
		super(DeviceNode, self).__init__()
		self.controller = controller
		self._protocol = ''
		self._model = ''
		self._protocolParams = {}

	def _command(self, action, value, success, failure, **__kwargs):
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

		def _success(__params):
			success()
		def fail():
			failure(Device.FAILED_STATUS_NO_REPLY)

		prefixes = {}
		if 'P' in msg:
			prefixes['P'] = msg['P']
		if 'R' in msg:
			prefixes['R'] = msg['R']
		if 'S' in msg:
			self.controller.queue(RF433Msg('S', msg['S'], prefixes, success=_success, failure=fail))

	def deviceType(self):
		protocol = Protocol.protocolInstance(self._protocol)
		if not protocol:
			return Device.TYPE_SWITCH_OUTLET
		protocol.setModel(self._model)
		return protocol.deviceType()

	@staticmethod
	def isDevice():
		return True

	@staticmethod
	def isSensor():
		return False

	def methods(self):
		protocol = Protocol.protocolInstance(self._protocol)
		if not protocol:
			return 0
		protocol.setModel(self._model)
		return protocol.methods()

	def model(self):
		return self._model

	def params(self):
		return {
			'type': 'device',
			'protocol': self._protocol,
			'model': self._model,
			'protocolParams': self._protocolParams,
		}

	def parameters(self):
		return self._protocolParams

	def protocol(self):
		return self._protocol

	def setParameter(self, name, value):
		if name not in ('code', 'fade', 'house', 'system', 'unit', 'units'):
			return
		self._protocolParams[name] = value
		self.paramUpdated(name)

	def setParams(self, params):
		self._protocol = params.setdefault('protocol', '')
		self._model = params.setdefault('model', '')
		self._protocolParams = params.setdefault('protocolParams', {})

class RF433(Plugin):
	implements(ITelldusLiveObserver)
	implements(ISignalObserver)

	fwVersions = {
		'18F25K50': 1
	}

	def __init__(self):
		self.version = 0
		self.hwVersion = None
		self.devices = []
		self.sensors = []
		self.rawEnabled = False
		self.rawEnabledAt = 0
		self.dev = Adapter(self, Board.rf433Port())
		self.deviceManager = DeviceManager(self.context)
		self.registerSensorCleanup()
		for dev in self.deviceManager.retrieveDevices('433'):
			params = dev.params()
			if 'type' not in params:
				continue
			if params['type'] == 'sensor':
				device = SensorNode()
				self.sensors.append(device)
			elif params['type'] == 'device':
				device = DeviceNode(self.dev)  # pylint: disable=R0204
				self.devices.append(device)
			else:
				continue
			device.setNodeId(dev.id())
			device.setParams(params)
			if params['type'] == 'sensor':
				# already loaded, keep it that way!
				device._packageCount = 7  # pylint: disable=W0212
				device._sensorValues = dev._sensorValues  # pylint: disable=W0212
				device.batteryLevel = dev.batteryLevel
				if hasattr(dev, 'declaredDead'):
					device.declaredDead = dev.declaredDead

			self.deviceManager.addDevice(device)

		self.deviceManager.finishedLoading('433')
		self.dev.queue(RF433Msg('V', success=self.__version, failure=self.__noVersion))
		self.dev.queue(RF433Msg('H', success=self.__hwVersion, failure=self.__noHWVersion))
		self.live = TelldusLive(self.context)

	def addDevice(self, uuid, protocol, model, name, params):
		device = DeviceNode(self.dev)
		if uuid:
			device.setUuid(uuid)
		device.setName(name)
		device.setParams({
			'protocol': protocol,
			'model': model,
			'protocolParams': params
		})
		self.devices.append(device)
		self.deviceManager.addDevice(device)

	def cleanupSensors(self):
		for i, sensor in enumerate(self.sensors):
			if not sensor.isValid():
				self.deviceManager.removeDevice(sensor.id())
				del self.sensors[i]

		self.deviceManager.sensorsUpdated()

	@TelldusLive.handler('rf433')
	def __handleCommand(self, msg):
		data = msg.argument(0).toNative()
		action = data['action']
		if action == 'addDevice':
			self.addDevice(data.get('id', None), data['protocol'], data['model'], data['name'], data['parameters'])

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

		elif action == 'rawEnabled':
			if data['value']:
				self.rawEnabled = True
				self.rawEnabledAt = time.time()
			else:
				self.rawEnabled = False

		else:
			logging.warning("Unknown rf433 command %s", action)

	@signal('rf433RawData')
	def decode(self, msg):
		"""
		Signal send on any raw data received from 433 receiver. Please note that
		the TellStick must contain a receiver for this signal to be sent. Not all
		models contains a receiver.
		"""
		if 'class' in msg and msg['class'] == 'sensor':
			self.decodeSensor(msg)
			return
		msg = Protocol.decodeData(msg)
		for cmdData in msg:
			self.decodeCommandData(cmdData)
			if self.rawEnabled:
				if self.rawEnabledAt < (time.time() - 600):
					# timeout, only allow scan for 10 minutes at a time
					self.rawEnabled = False
					continue
				self.live.pushToWeb('client', 'rawData', cmdData)

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
				convertedParameter = deviceParams[parameter]
				try:
					convertedParameter = str(convertedParameter)
				except Exception as __error:
					pass
				if msg[parameter] != convertedParameter:
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
		protocol = data['protocol']
		model = data['model']
		sensorId = data['id']
		sensorData = data['values']
		sensor = None
		for lsensor in self.sensors:
			if lsensor.compare(protocol, model, sensorId):
				sensor = lsensor
				break
		if sensor is None:
			sensor = SensorNode()
			sensor.setParams({'protocol': protocol, 'model': model, 'sensorId': sensorId})
			sensor.setManager(self.deviceManager)
			self.sensors.append(sensor)
		if 'battery' in data:
			sensor.batteryLevel = data['battery']
		sensor.updateValues(sensorData)

	def registerSensorCleanup(self):
		"""Register scheduled job to clean up sensors that have not been updated for a while"""
		Application().registerScheduledTask(self.cleanupSensors, hours=12)  # every 12th hour
		tmr = Timer(600, self.cleanupSensors)  # run a first time after 10 minutes
		tmr.daemon = True
		tmr.name = 'Sensor cleanup'
		tmr.start()

	@staticmethod
	def __noVersion():
		logging.warning("Could not get firmware version for RF433, force upgrade")

	@staticmethod
	def __noHWVersion():
		logging.warning("Could not get hw version for RF433")

	def __hwVersion(self, version):
		logging.debug("Got HW version %s", version)
		self.hwVersion = version
		if version not in RF433.fwVersions:
			return
		fwVersion = RF433.fwVersions[self.hwVersion]
		if fwVersion != self.version:
			logging.info("Version %i is to old, update firmware", self.version)
			# TODO: implement

	def __version(self, version):
		self.version = version
		logging.info("RF433 version: %i", self.version)

	def __loadDeviceByUUID(self, uuid, protocol, model, parameters):
		self.addDevice(uuid, protocol, model, 'provisioning', parameters)

	@slot('provisioning', profile='rf433')
	def __provisioning(self, data):
		for deviceData in data.get('devices', []):
			found = False
			for device in self.devices:
				uuid = UUID(deviceData.get('id'))
				if device.uuid() == uuid:
					found = True
					break
			if found:
				continue
			self.__loadDeviceByUUID(
			    deviceData['id'], deviceData['protocol'], deviceData['model'],
			    deviceData['parameters']
			)
