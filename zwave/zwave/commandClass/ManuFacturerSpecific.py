from pyzwave.const.ZW_classcmd import COMMAND_CLASS_MANUFACTURER_SPECIFIC
from . import CommandClass, ZWaveCommandClass


@ZWaveCommandClass(COMMAND_CLASS_MANUFACTURER_SPECIFIC)
class ManufacturerSpecific(CommandClass):
	async def zwaveInfo(self):
		return {
		    'manufacturerId': self.native.manufacturerID,
		    'productTypeId': self.native.productTypeID,
		    "productId": self.native.productID,
		    "version": self.native.version,
		    "interviewed": self.native.interviewed,
		}
