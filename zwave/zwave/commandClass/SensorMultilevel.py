import logging

from telldus import Device
from pyzwave.const.ZW_classcmd import COMMAND_CLASS_SENSOR_MULTILEVEL
from pyzwave.commandclass.SensorMultilevel import SensorType
import pyzwave.commandclass.SensorMultilevel
from . import CommandClass, ZWaveCommandClass

_LOGGER = logging.getLogger(__name__)

SENSOR_MAPPING = {
    SensorType.TEMPERATURE: Device.TEMPERATURE,
    SensorType.HUMIDITY: Device.HUMIDITY,
    SensorType.LUMINANCE: Device.LUMINANCE,
    SensorType.UV: Device.UV,
    SensorType.VELOCITY: Device.WINDAVERAGE,
    SensorType.BAROMETRIC_PRESSURE: Device.BAROMETRIC_PRESSURE,
    SensorType.DEW_POINT: Device.DEW_POINT,
    SensorType.POWER: Device.WATT,
    SensorType.PM25: Device.PM25,
    SensorType.WEIGHT: Device.WEIGHT,
    SensorType.CO: Device.CO,
    SensorType.VOLUME: Device.VOLUME,
    SensorType.LOUDNESS: Device.LOUDNESS,
    SensorType.MOISTURE: Device.MOISTURE,
    SensorType.RAIN_RATE: Device.RAINRATE,
    SensorType.VOLTAGE: Device.WATT,
}


@ZWaveCommandClass(COMMAND_CLASS_SENSOR_MULTILEVEL)
class SensorMultilevel(CommandClass):
	async def onReport(
	    self, _, report: pyzwave.commandclass.SensorMultilevel.Report
	):
		valueType = SENSOR_MAPPING.get(SensorType(report.sensorType), Device.UNKNOWN)
		scale = report.sensorValue.scale

		# Do some scale converting, if needed
		if report.sensorType == SensorType.POWER:
			if scale == 0:
				scale = 2
			else:
				return True
		elif report.sensorType == SensorType.CO2:
			if scale == 0:
				# CO and CO2 uses the same scale (PPM),
				# but Z-Wave have different scale values for these
				# Let's normalize that...
				scale = 1
		elif valueType == SensorType.VOLTAGE:
			scale = Device.SCALE_POWER_VOLT

		self.device.setSensorValue(valueType, report.sensorValue, scale)
		return True
