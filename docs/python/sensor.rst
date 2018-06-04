Sensor Plugin Development
=========================


Prepare the Sensor
##################

In order to create the sensor, you have to import ``Sensor`` class form the ``telldus`` Package
and Extend it in your SesorDevice Class

.. code::

  from base import Plugin, Application
  from telldus import DeviceManager, Sensor

  class DummySensor(Sensor):
    def __init__(self):
      super(TemperatureSensor,self).__init__()

    ...
    ...
    ...

Export a functions
##################

All sensors exported must subclass Sensor 

Minimal function to reimplement is : 
``_command`` ,
``localId`` ,
``typeString`` ,
``methods``

.. code::

  def _command(self, action, value, success, failure, **kwargs):
    '''This method is called when someone want to control this sensor

    action is the method id to execute. This could be for instance:
    Sensor.TURNON or Sensor.TURNOFF

    value is only used for some actions, for example dim

    This method _must_ call either success or failure
    '''
    logging.debug('Sending command %s to dummy sensor', action)
    success()

  def localId(self):
    '''Return a unique id number for this sensor. The id should not 
    be globally unique but only unique for this sensor type.
    '''
    return 0

  def typeString(self):
    '''Return the sensor type. Only one plugin at a time may export sensors using
    the same typestring'''
    return 'dummySensor'

  def methods(self):
    '''Return a bitset of methods this sensor supports'''
    return Sensor.TURNON | Sensor.TURNOFF



Add Sensor 
##########

To add a sensor into plugin ``Dummy``: 


.. code::

  class Dummy(Plugin):
    '''This is the plugins main entry point and is a singleton
    Manage and load the plugins here
    '''
    def __init__(self):
      # The devicemanager is a globally manager handling all device types
      self.deviceManager = DeviceManager(self.context)

      # Load all devices this plugin handles here. Individual settings for the devices
      # are handled by the devicemanager
      self.deviceManager.addDevice(DummySensor())

      # When all devices has been loaded we need to call finishedLoading() to tell
      # the manager we are finished. This clears old devices and caches
      self.deviceManager.finishedLoading('dummySensor')



A complete example for Temprature sensor
########################################

.. code::

  # -*- coding: utf-8 -*-

  import math
  import time

  from base import Application, Plugin
  from telldus import DeviceManager, Sensor

  class TemperatureSensor(Sensor):
    '''All sensors exported must subclass Sensor

    Minimal function to reimplement is:
    localId
    typeString
    '''
    @staticmethod
    def localId():
      '''Return a unique id number for this sensor. The id should not be
      globally unique but only unique for this sensor type.
      '''
      return 2

    @staticmethod
    def typeString():
      '''Return the sensor type. Only one plugin at a time may export sensors using
      the same typestring'''
      return 'temperature'

    def updateValue(self):
      """setTempratureSensor value constantly."""
      # This is dummy data
      self.setSensorValue(Sensor.TEMPERATURE, 35, Sensor.SCALE_TEMPERATURE_CELCIUS)

  class Temperature(Plugin):
    '''This is the plugins main entry point and is a singleton
    Manage and load the plugins here
    '''
    def __init__(self):
      # The devicemanager is a globally manager handling all device types
      self.deviceManager = DeviceManager(self.context)

      # Load all devices this plugin handles here. Individual settings for the devices
      # are handled by the devicemanager
      self.sensor = TemperatureSensor()
      self.deviceManager.addDevice(self.sensor)

      # When all devices has been loaded we need to call finishedLoading() to tell
      # the manager we are finished. This clears old devices and caches
      self.deviceManager.finishedLoading('temperature')

      Application().registerScheduledTask(self.updateValues, minutes=1, runAtOnce=True)

    def updateValues(self):
      self.sensor.updateValue()
