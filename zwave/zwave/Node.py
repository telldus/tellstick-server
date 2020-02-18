# -*- coding: utf-8 -*-

import logging

from pyzwave.commandclass import SwitchBinary
from pyzwave.const.ZW_classcmd import COMMAND_CLASS_SENSOR_MULTILEVEL, COMMAND_CLASS_METER
import pyzwave.node

from zwave.commandClass import CommandClass

from telldus import Device

_LOGGER = logging.getLogger(__name__)


class Node(Device):
	def __init__(self, node: pyzwave.node.Node):
		super().__init__()
		self._node = node
		self._supported = {}
		for cmdClassId, cmdClass in self._node.supported.items():
			self._supported[cmdClassId] = CommandClass.load(cmdClassId, cmdClass, self)

	async def _command(self, action, value, **_kwargs):  # pylint: disable=arguments-differ
		if action == Device.TURNON:
			return await self.node.send(SwitchBinary.Set(value=0xFF))
		elif action == Device.TURNOFF:
			return await self.node.send(SwitchBinary.Set(value=0))
		return False

	async def interview(self, cmdClass):
		if cmdClass:
			await self._node.supported[cmdClass].interview()
		else:
			await self._node.interview()

	def localId(self) -> str:
		return self._node.nodeId

	def isSensor(self) -> bool:
		if self._node.supports(COMMAND_CLASS_SENSOR_MULTILEVEL):
			return True
		if self._node.supports(COMMAND_CLASS_METER):
			return True
		return False

	def typeString(self) -> str:
		return "zwave"

	def methods(self) -> int:
		return Device.TURNON | Device.TURNOFF

	@property
	def node(self) -> pyzwave.node.Node:
		return self._node

	async def zwaveInfo(self):
		params = {
		    'basicDeviceClass': self.node.basicDeviceClass,
		    'genericDeviceClass': self.node.genericDeviceClass,
		    'specificDeviceClass': self.node.specificDeviceClass,
		    'cmdClasses':
		    {x: await self._supported[x].zwaveInfo()
		     for x in self._supported},
		    'listening': bool(self.node.listening),
		    'flirs': self.node.flirs,
		    'nodeId': self.node.nodeId,
		    # 'nodeType': self.node.nodeType,
		    'isFailed': self.node.isFailed,
		    # 'isSupported': self.__isSupportedType()
		}
		# if ':' in self.node.nodeId:
		# 	# Subnode. Add the parent node device id
		# 	device = self.handler.deviceByNodeId(self.node.parentNode.nodeId)
		# 	if device:
		# 		params['parentDeviceId'] = device.id()
		return params
