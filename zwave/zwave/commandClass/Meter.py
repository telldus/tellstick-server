import logging

from telldus import Device
from pyzwave.const.ZW_classcmd import COMMAND_CLASS_METER
from pyzwave.commandclass.Meter import MeterType
import pyzwave.commandclass.Meter
from . import CommandClass, ZWaveCommandClass

_LOGGER = logging.getLogger(__name__)


@ZWaveCommandClass(COMMAND_CLASS_METER)
class Meter(CommandClass):
	async def onReport(
	    self, _, report: pyzwave.commandclass.SensorMultilevel.Report
	):
		if report.meterType != MeterType.ELECTRIC_METER:
			_LOGGER.warning("Unknown meter type received: %s", report.meterType)
			return False
		self.device.setSensorValue(Device.POWER, report.meterValue, report.scale)

		return True
