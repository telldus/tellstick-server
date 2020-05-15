import logging

from pyzwave.const.ZW_classcmd import COMMAND_CLASS_CONFIGURATION
from . import CommandClass, ZWaveCommandClass

_LOGGER = logging.getLogger(__name__)


@ZWaveCommandClass(COMMAND_CLASS_CONFIGURATION)
class Configuration(CommandClass):
	async def doCommand(self, command, data):
		if command == 'setConfigurations':
			for cfg in data:
				try:
					number = int(cfg['number'])
					size = int(cfg['size'])
					value = int(cfg['value'])
				except Exception as _error:
					continue
				await self.native.set(number, size, value)
		elif command == 'getConfiguration':
			try:
				number = int(data['number'])
			except Exception as _error:
				return
			value = await self.native.get(number, cached=False)
