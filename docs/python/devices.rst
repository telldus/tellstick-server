==================================
Methods, actions and sensor values
==================================

The core object in tellstick-server is the :class:`Device <telldus.Device>` object.

Device vs sensor?
=================

In Telldus Live! devices and sensors are separated and two separate things. In tellstick-server
these are one object and all inherits :class:`telldus.Device`.

There is a convenience class :class:`telldus.Sensor` that sets some initial parameters for devices
that only supports sensor-values.

Methods
=======

TellStick can control many different types of devices that support different features. For example,
a bell does not support the on-signal and not all lamp switches support dimming.

To determine which methods a device supports, call the function
:func:`methods() <telldus.Device.methods>` on the device.

See the following example to determine if a device supports on and off:

.. code-block:: python
  :caption: Python example:

  methods = device.methods()
  if methods & Device.TURNON:
    logging.debug('The device supports turning on')
  if methods & Device.TURNON:
    logging.debug('The device supports turning off')
  if methods & Device.DIM:
    logging.debug('The device is dimmable')

.. code-block:: lua
  :caption: Lua example:

  ON = 1
  OFF = 2
  DIM = 16

  local methods = device:methods()
  if (BitAND(methods, ON) == ON) then
    print("The device supports turning on")
  end
  if (BitAND(methods, OFF) == OFF) then
    print("The device supports turning off")
  end
  if (BitAND(methods, DIM) == DIM) then
    print("The device is dimmable")
  end

  -- The lua version shipped with TellStick does not support bitwise operators
  function BitAND(a,b)--Bitwise and
    local p,c=1,0
    while a>0 and b>0 do
      local ra,rb=a%2,b%2
      if ra+rb>1 then c=c+p end
      a,b,p=(a-ra)/2,(b-rb)/2,p*2
    end
    return c
  end
