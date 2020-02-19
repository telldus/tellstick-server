import logging

from telldus import Device
from pyzwave.const.ZW_classcmd import COMMAND_CLASS_SWITCH_BINARY
import pyzwave.commandclass.SwitchBinary
from . import CommandClass, ZWaveCommandClass

_LOGGER = logging.getLogger(__name__)


@ZWaveCommandClass(COMMAND_CLASS_SWITCH_BINARY)
class SwitchBinary(CommandClass):
	async def onReport(self, _, report: pyzwave.commandclass.SwitchBinary.Report):
		if report.value == 0xFF:
			self.device.setState(Device.TURNON, None)
			return True
		if report.value == 0x00:
			self.device.setState(Device.TURNOFF, None)
			return True
		# Not handled
		return False
