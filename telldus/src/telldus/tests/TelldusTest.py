# -*- coding: utf-8 -*-

import time
import unittest
import pytz

from datetime import datetime, timedelta
from freezegun import freeze_time
from tzlocal import get_localzone

from ..Device import Device

# run this with python -m unittest telldus.tests in the tellstick.sh-shell

class MockDeviceManager(object):
	def __init__(self):
		self.values = None

	def sensorValuesUpdated(self, __device, values):
		self.values = values

	def save(self):
		pass

class TelldusTest(unittest.TestCase):
	def setUp(self):
		self.device = Device()
		self.device.setManager(MockDeviceManager())

	def tearDown(self):
		pass

	def testSensorMessage(self):
		values = [{'scale': 0, 'type': 1, 'value': '21.3'}, {'scale': 0, 'type': 2, 'value': '46'}]
		self.device.setSensorValues(values)
		self.assertEqual(values, self.device.manager().values,
		   "Initial values were not passed on to the server")

		self.device.manager().values = []  # reset
		self.device.setSensorValues(values)
		self.assertEqual([], self.device.manager().values,
		   "Values passed on to server dispite not one second since last report")
		with freeze_time(datetime.now(pytz.timezone(str(get_localzone()))) + timedelta(0, 2)):
			self.device.manager().values = []  # reset
			self.device.setSensorValues(values)
			self.assertEqual(values, self.device.manager().values,
			   "Values not passed on to server dispite two seconds since last report")

		values = [{'scale': 0, 'type': 1, 'value': '21.3'}, {'scale': 0, 'type': 2, 'value': '46'}]
		self.device.manager().values = []  # reset
		self.device.setSensorValues(values)
		self.assertEqual([], self.device.manager().values,
		   "Values passed on to server dispite no value changed")

		values = [{'scale': 0, 'type': 1, 'value': '22.3'}, {'scale': 0, 'type': 2, 'value': '46'}]
		self.device.manager().values = []  # reset
		self.device.setSensorValues(values)
		self.assertEqual(values, self.device.manager().values,
		   "Values not passed on to server dispite one value changed")

		values = [{'scale': 0, 'type': 1, 'value': '22.3'}, {'scale': 0, 'type': 2, 'value': '47'}]
		self.device.manager().values = []  # reset
		self.device.setSensorValues(values)
		self.assertEqual(values, self.device.manager().values,
		   "Values not passed on to server dispite another value changed")

		values = [{'scale': 0, 'type': 1, 'value': '22.3'}, {'scale': 0, 'type': 2, 'value': '47'}]
		self.device.setSensorValues(values)
		element = {}
		element['scale'] = 0
		element['type'] = 1
		element['lastUpdated'] = int(time.time())
		element['value'] = '22.3'
		self.device._sensorValues[1] = [element]  # pylint: disable=protected-access
		element = {}
		element['scale'] = 0
		element['type'] = 2
		element['lastUpdated'] = int(time.time() - 2)
		element['value'] = '47'
		self.device._sensorValues[2] = [element]  # pylint: disable=protected-access
		self.device.manager().values = []  # reset
		self.device.setSensorValues(values)
		self.assertEqual(values, self.device.manager().values,
		   "Values not passed on, even though one value was updated more than 1 second ago")

		values = [{'scale': 0, 'type': 1, 'value': '22.3'}, {'scale': 0, 'type': 2, 'value': '47'}]
		self.device.setSensorValues(values)
		element = {}
		element['scale'] = 0
		element['type'] = 1
		element['lastUpdated'] = int(time.time()-2)
		element['value'] = '22.3'
		self.device._sensorValues[1] = [element]  # pylint: disable=protected-access
		element = {}
		element['scale'] = 0
		element['type'] = 2
		element['lastUpdated'] = int(time.time())
		element['value'] = '47'
		self.device._sensorValues[2] = [element]  # pylint: disable=protected-access
		self.device.manager().values = []  # reset
		self.device.setSensorValues(values)
		self.assertEqual(values, self.device.manager().values,
		   "Values not passed on, even though another value was updated more than 1 second ago")
