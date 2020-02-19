# pylint: disable=invalid-name

from telldus import Device
import pyzwave.commandclass


class CommandClassCollection(dict):
	"""
    Decorator for registering a CommandClass to the system
    """
	def __call__(self, cmdClass):
		def decorator(cls):
			self[cmdClass] = cls
			return cls

		return decorator


ZWaveCommandClass = CommandClassCollection()  # pylint: disable=invalid-name


class CommandClass:
	def __init__(
	    self, commandClass: pyzwave.commandclass.CommandClass, device: Device
	):
		self._commandClass = commandClass
		self._device = device
		commandClass.addListener(self)

	@property
	def device(self) -> Device:
		return self._device

	@property
	def native(self) -> pyzwave.commandclass.CommandClass:
		"""Returns the node this command class belongs to"""
		return self._commandClass

	async def version(self) -> int:
		version = self.native.version
		if version == 0:
			version = await self.native.requestVersion()
		return version

	async def zwaveInfo(self):
		return self.native.__getstate__()

	@staticmethod
	def load(
	    cmdClass: int, commandClass: pyzwave.commandclass.CommandClass, device
	) -> object:
		CommandClassCls = ZWaveCommandClass.get(cmdClass, CommandClass)
		return CommandClassCls(commandClass, device)


# pylint: disable=wrong-import-position
from . import ManuFacturerSpecific, SensorMultilevel, SwitchBinary
