# -*- coding: utf-8 -*-

import logging

import pyzwave.application
import pyzwave.zipgateway
import pyzwave.persistantstorage
from pyzwave.const import ZW_classcmd

from base import Application, Plugin, implements
from board import Board
from telldus import DeviceManager
from tellduslive.base import ITelldusLiveObserver, TelldusLive
from .Node import Node

_LOGGER = logging.getLogger(__name__)

PSK = "123456789012345678901234567890AA"


class Manager(Plugin):
	implements(ITelldusLiveObserver)

	def __init__(self):
		self.app = None
		self.nodes = {}
		Application().createTask(self.startup)
		Application().registerShutdown(self.shutdown)

	@TelldusLive.handler('zwave')
	def __handleCommand(self, msg):
		data = msg.argument(0).toNative()
		action = data['action']
		if action == 'addNodeToNetwork':
			#self.controller.addNodeToNetwork(1 | 0x80 | 0x40, secure=False)
			pass

		# elif action == 'addSecureNodeToNetwork':
		# 	#self.controller.addNodeToNetwork(1 | 0x80 | 0x40, secure=True)
		# 	pass

		# elif action == 'addNodeToNetworkStop':
		# 	#self.controller.addNodeToNetwork(5)
		# 	pass

		# elif action == 'basic':
		# 	#self.__handleCommandBasic(data)
		# 	pass

		# elif action == 'cmdClass':
		# 	# self.__handleCommandCmdClass(data)
		# 	pass

		# elif action == 'getRoutingInfo':
		# 	# self.__handleCommandGetRoutingInfo(data)
		# 	pass

		elif action == 'interview':
			Application().createTask(self.__handleInterview, data)

		# elif action == 'markNodeAsFailed':
		# 	# self.__handleCommandMarkNodeAsFailed(data)
		# 	pass

		# elif action == 'meter':
		# 	# self.__handleCommandMeter(data)
		# 	pass

		elif action == 'nodeInfo':
			Application().createTask(self.__handleCommandNodeInfo, data)

		# elif action == 'nodeList':
		# 	# self.__handleCommandNodeList()
		# 	pass

		# elif action == 'removeFailedNode':
		# 	# self.__handleCommandRemoveFailedNode(data)
		# 	pass

		# elif action == 'removeNodeFromNetwork':
		# 	# self.controller.removeNodeFromNetwork(1)
		# 	pass

		# elif action == 'removeNodeFromNetworkStop':
		# 	# self.controller.removeNodeFromNetwork(5)
		# 	pass

		# elif action == 'replaceFailedNode':
		# 	# self.__handleCommandReplaceFailedNode(data)
		# 	pass

		# elif action == 'requestNodeInfo':
		# 	# self.__handleCommandRequestNodeInfo(data)
		# 	pass

		# elif action == 'requestNodeNeighborUpdate':
		# 	# self.__handleCommandRequestNodeNeighborUpdate(data)
		# 	pass

		# elif action == 'startLearnMode':
		# 	# self.controller.startLearnMode()
		# 	pass

		# elif action == 'controllerReset':
		# 	# self.controller.reset()
		# 	pass
		# elif action == 'controllerShift':
		# 	# self.controller.shift()
		# 	pass
		# elif action == 'requestNetworkUpdate':
		# 	# self.controller.requestNetworkUpdate()
		# 	pass
		# elif action == 'sendNIF':
		# 	# self.controller.sendNIF()
		# 	pass

		else:
			print("Unhandled action", action)

	async def __handleCommandNodeInfo(self, data):
		if 'device' not in data:
			return
		deviceManager = DeviceManager(self.context)  # pylint: disable=too-many-function-args
		device = deviceManager.device(data['device'])
		if device is None:
			return
		nodeInfo = await device.zwaveInfo()
		nodeInfo['deviceId'] = data['device']
		TelldusLive(self.context).pushToWeb('zwave', 'nodeInfo', nodeInfo)  # pylint: disable=too-many-function-args

	async def __handleInterview(self, data):
		if 'device' not in data:
			return
		deviceManager = DeviceManager(self.context)  # pylint: disable=too-many-function-args
		device = deviceManager.device(data['device'])
		if not device:
			return
		if not isinstance(device, Node):
			return
		cmdClass = data['class'] if 'class' in data else None
		await device.interview(cmdClass)

	async def nodeAdded(
	    self, _: pyzwave.application.Application, node: pyzwave.node.Node
	):
		device = Node(node)
		self.nodes[node.nodeId] = device
		deviceManager = DeviceManager(self.context)  # pylint: disable=too-many-function-args
		deviceManager.addDevice(device)

	async def nodeRemoved(self, _: pyzwave.application.Application, nodeId: str):
		device = self.nodes.get(nodeId)
		if not device:
			return
		deviceManager = DeviceManager(self.context)  # pylint: disable=too-many-function-args
		deviceManager.removeDevice(device.id())
		del self.nodes[nodeId]

	async def startup(self):
		# pylint: disable=too-many-function-args
		deviceManager = DeviceManager(self.context)
		adapter = pyzwave.zipgateway.ZIPGateway(
		    "192.168.0.169", psk=bytes.fromhex(PSK)
		)
		await adapter.connect()
		storage = pyzwave.persistantstorage.YamlStorage(Board.configDir())
		self.app = pyzwave.application.Application(adapter, storage)
		self.app.setNodeInfo(
		    generic=ZW_classcmd.GENERIC_TYPE_STATIC_CONTROLLER,
		    specific=ZW_classcmd.SPECIFIC_TYPE_GATEWAY,
		    cmdClasses=[
		        ZW_classcmd.COMMAND_CLASS_ZWAVEPLUS_INFO,
		        ZW_classcmd.COMMAND_CLASS_VERSION,
		        ZW_classcmd.COMMAND_CLASS_MANUFACTURER_SPECIFIC,
		        ZW_classcmd.COMMAND_CLASS_DEVICE_RESET_LOCALLY,
		        ZW_classcmd.COMMAND_CLASS_ASSOCIATION_GRP_INFO,
		        ZW_classcmd.COMMAND_CLASS_ASSOCIATION,
		        ZW_classcmd.COMMAND_CLASS_SECURITY,
		        ZW_classcmd.COMMAND_CLASS_CRC_16_ENCAP,
		        ZW_classcmd.COMMAND_CLASS_POWERLEVEL,
		    ],
		)
		self.app.addListener(self)
		await self.app.startup()
		deviceManager.finishedLoading("zwave")

	async def shutdown(self):
		if self.app:
			await self.app.shutdown()
