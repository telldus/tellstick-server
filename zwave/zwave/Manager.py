# -*- coding: utf-8 -*-

import logging

import pyzwave.application
import pyzwave.zipgateway
import pyzwave.persistantstorage
from pyzwave.const import ZW_classcmd
from pyzwave.adapter import TxOptions
from pyzwave.message import Message
from pyzwave.commandclass.NetworkManagementInclusion import (
    NodeAddDSKReport, NodeAddKeysReport, NodeAddStatus, NodeRemoveStatus
)

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
		self.app: pyzwave.application.Application = None
		self.nodes = {}
		self.secureInclusion = False
		Application().createTask(self.startup)
		Application().registerShutdown(self.shutdown)

	@TelldusLive.handler('zwave')
	def __handleCommand(self, msg):
		data = msg.argument(0).toNative()
		action = data['action']
		if action == 'addNodeToNetwork':
			self.secureInclusion = False
			Application().createTask(self.__handleAddNode)

		elif action == 'addSecureNodeToNetwork':
			self.secureInclusion = True
			Application().createTask(self.__handleAddNode)

		elif action == 'addNodeToNetworkStop':
			Application().createTask(self.app.adapter.addNodeStop)

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

		elif action == 'removeNodeFromNetwork':
			Application().createTask(self.__handleRemoveNodeFromNetwork)

		elif action == 'removeNodeFromNetworkStop':
			Application().createTask(self.app.adapter.removeNodeStop)

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

	async def addNodeStatus(self, _speaker, status: NodeAddStatus):
		if status.status == NodeAddStatus.Status.DONE:
			# These 3 messages is not received by zipgateway, we need to create them ourself
			self.pushToWeb('addNodeToNetwork', [NodeAddStatus.Status.NODE_FOUND, 0, 0])
			self.pushToWeb(
			    'addNodeToNetwork', [
			        NodeAddStatus.Status.ADD_SLAVE, status.newNodeID,
			        len(status.commandClass) + 3, status.basicDeviceClass,
			        status.genericDeviceClass, status.specificDeviceClass,
			        *status.commandClass
			    ]
			)
			self.pushToWeb(
			    'addNodeToNetwork',
			    [NodeAddStatus.Status.PROTOCOL_DONE, status.newNodeID, 0]
			)

			self.pushToWeb(
			    'addNodeToNetwork', [NodeAddStatus.Status.DONE, status.newNodeID, 0]
			)
		else:
			self.pushToWeb('addNodeToNetwork', [status.status, status.newNodeID, 0])

	async def removeNodeStatus(self, _speaker, status: NodeRemoveStatus):
		self.pushToWeb('removeNodeFromNetwork', [status.status, status.nodeID, 0])

	async def __handleAddNode(self):
		ret = await self.app.adapter.addNode(TxOptions.TRANSMIT_OPTION_EXPLORE)
		if ret:
			self.pushToWeb('addNodeToNetwork', [1, 0, 0])

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
		device: Node = deviceManager.device(data['device'])
		if not device:
			return
		if not isinstance(device, Node):
			return
		cmdClass = data['class'] if 'class' in data else None
		await device.interview(cmdClass)

	async def __handleRemoveNodeFromNetwork(self):
		ret = await self.app.adapter.removeNode()
		if ret:
			self.pushToWeb('removeNodeFromNetwork', [1, 0, 0])

	async def __handleSecureInclusion(self, report: NodeAddKeysReport):
		if not self.secureInclusion:
			await self.app.adapter.addNodeKeysSet(False, False, 0)
			return True
		await self.app.adapter.addNodeKeysSet(False, True, report.requestedKeys)
		return True

	async def messageReceived(self, _sender, message: Message):
		if isinstance(message, NodeAddKeysReport):
			return await self.__handleSecureInclusion(message)
		if isinstance(message, NodeAddDSKReport):
			if message.inputDSKLength == 0:
				# Unauthenticated S2
				await self.app.adapter.addNodeDSKSet(True, 0, b'')
			return True
		return False

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
