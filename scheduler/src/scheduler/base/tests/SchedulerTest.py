# -*- coding: utf-8 -*-

import unittest
import os
import pytz
import time
from dateutil import parser
from freezegun import freeze_time
from mock import MagicMock, Mock, patch
from tzlocal import get_localzone
from ..SchedulerEventFactory import BlockheaterTrigger, \
   SuntimeTrigger, TimeCondition, TimeTrigger, TimeTriggerManager
from telldus import Device

# run this with python -m unittest scheduler.base.tests in the tellstick.sh-shell

class MockDeviceManager(object):
	def __init__(self):
		self.sensor = MockSensor()

	def device(self, sensorId):
		return self.sensor

	def setLastUpdated(self, lastUpdated):
		self.sensor.setLastUpdated(lastUpdated)

	def setValue(self, value):
		self.sensor.setSensorValue(value)


class MockSensor(Device):
	def __init__(self):
		super(MockSensor, self).__init__()
		self.value = -10
		self._sensorValues = {1: [{'lastUpdated': time.time(), 'scale': 0, 'value': self.value}], \
		   2: [{'lastUpdated': time.time(), 'scale': 0, 'value': 27}]}

	def sensorValue(self, type, scale):
		return self.value

	def setLastUpdated(self, lastUpdated):
		self._sensorValues[1][0]['lastUpdated'] = lastUpdated

	def setSensorValue(self, value):
		self.value = value
		self._sensorValues[1][0]['value'] = value

class MockSettings(object):
	def __init__(self, defaultTimezone):
		self.timezone = defaultTimezone  # default

	def get(self, setting, defaultValue):
		if setting == 'tz':
			return self.timezone
		elif setting == 'latitude':
			return 55.70584
		elif setting == 'longitude':
			return 13.19321

class ModifiedBlockheaterTrigger(BlockheaterTrigger):
	def __init__(self, timezone, *args, **kwargs):
		self.usertimezone = timezone
		super(ModifiedBlockheaterTrigger, self).__init__(*args, **kwargs)

	def getSettings(self):
		return MockSettings(self.usertimezone)

class SchedulerTest(unittest.TestCase):
	def __init__(self, *args, **kwargs):
		os.environ['TZ'] = 'UTC'  # set local environment to UTC for tests
		time.tzset()
		self.usertimezone = 'Europe/Stockholm'
		super(SchedulerTest, self).__init__(*args, **kwargs)

	def setUp(self, mocked_settings=None):
		# this is run once per test-method
		kwargs = {'event': None, 'id': None, 'group': None}
		# THIS OR GET SETTING, or even better, get timezone...
		#from scheduler.base import SchedulerEventFactory
		#SchedulerEventFactory.Setting = MockSettings
		#from scheduler.base.SchedulerEventFactory import TimeCondition
		#TimeCondition.Settings = MagicMock
		TimeCondition.getSettings = lambda dummy: MockSettings(self.usertimezone)
		self.timeCondition = TimeCondition(**kwargs)
		TimeTrigger.getSettings = lambda dummy: MockSettings(self.usertimezone)
		mockEvent = Mock()
		mockEvent.execute = Mock()
		kwargs = {'params': {'minute': '0', 'hour': '11'}, 'event': mockEvent, 'id': 833}
		self.timeTrigger = TimeTrigger(TimeTriggerManager(False), **kwargs)
		mockEvent = Mock()
		mockEvent.execute = Mock()
		kwargs = {'params': {'minute': '0', 'hour': '11'}, 'event': mockEvent, 'id': 833}
		self.sunTimeTrigger = SuntimeTrigger(TimeTriggerManager(False), **kwargs)

	def tearDown(self):
		pass

	def checkTime(self, hour, minute):
		self.assertEqual(self.blockHeaterTrigger.setHour, hour)
		self.assertEqual(self.blockHeaterTrigger.minute, minute)
		# manager list:
		self.assertNotEqual(self.blockHeaterTrigger.manager.triggers.get(minute, None), None)

	def freezeTimeSimplifier(self, tstr):
		return pytz.timezone(self.usertimezone).localize(parser.parse(tstr)).astimezone(pytz.utc)

	def resetTrigger(self, temp=None, timezone='UTC', lastUpdated=time.time()):
		factory = None
		manager = TimeTriggerManager(False)
		deviceManager = MockDeviceManager()
		if temp != None:
			deviceManager.setValue(temp)
		deviceManager.setLastUpdated(lastUpdated)
		mockEvent = Mock()
		mockEvent.execute = Mock()
		kwargs = {'params': {'sensorId': '1000348', 'clientSensorId': 97, 'minute': '0', 'hour': '11'}, \
		   'event': mockEvent, 'id': 833}
		self.blockHeaterTrigger = ModifiedBlockheaterTrigger(timezone, factory, manager, \
		   deviceManager, **kwargs)
		self.blockHeaterTrigger.parseParam('clientSensorId', 1)
		self.blockHeaterTrigger.parseParam('hour', 8)
		self.blockHeaterTrigger.parseParam('minute', 0)

	def validateCondition(self, testEnvironmentTimestring, result, forceUTC=False):
		if forceUTC:
			testEnvironmentTZ = pytz.timezone('UTC')
		else:
			testEnvironmentTZ = pytz.timezone(str(get_localzone()))
		testEnvironmentTime = parser.parse(testEnvironmentTimestring)
		testEnvironmentTimeAware = testEnvironmentTZ.localize(testEnvironmentTime)
		response = Mock()
		with freeze_time(testEnvironmentTimeAware.astimezone(pytz.utc)):
			self.timeCondition.validate(response.success, response.failure)
			if result:
				self.assertTrue(response.success.called, testEnvironmentTimestring + " not correct")
				self.assertFalse(response.failure.called)
			else:
				self.assertFalse(response.success.called, testEnvironmentTimestring + " not correct")
				self.assertTrue(response.failure.called)

	def testTimeCondition(self):
		localTimezone = str(get_localzone())

		# Test for condition interval, near the limits and general
		# set up:
		self.timeCondition.timezone = localTimezone
		self.timeCondition.fromHour = 23
		self.timeCondition.fromMinute = 10
		self.timeCondition.toHour = 5
		self.timeCondition.toMinute = 15
		# tests:
		self.validateCondition("2018-10-10 23:09", False)
		self.validateCondition("2018-10-10 23:10", True)
		self.validateCondition("2018-10-10 23:11", True)
		self.validateCondition("2018-10-05 05:14", True)
		self.validateCondition("2018-10-05 05:15", True)
		self.validateCondition("2018-10-05 05:16", False)
		self.validateCondition("2018-10-05 01:16", True)
		self.validateCondition("2018-10-05 02:16", True)

		# Test for condition interval passing midnight
		# set up:
		self.timeCondition.timezone = localTimezone
		self.timeCondition.fromHour = 23
		self.timeCondition.fromMinute = 55
		self.timeCondition.toHour = 0
		self.timeCondition.toMinute = 15
		# tests:
		self.validateCondition("2018-10-05 23:54", False)
		self.validateCondition("2018-10-05 23:57", True)
		self.validateCondition("2018-10-05 00:07", True)
		self.validateCondition("2018-10-05 00:16", False)

		# Test for condition interval in timezone offset
		# set up:
		self.timeCondition.timezone = localTimezone
		self.timeCondition.fromHour = 0
		self.timeCondition.fromMinute = 5
		self.timeCondition.toHour = 0
		self.timeCondition.toMinute = 15
		# tests:
		self.validateCondition("2018-10-05 00:01", False)
		self.validateCondition("2018-10-05 00:07", True)
		self.validateCondition("2018-10-05 00:16", False)

		# Test for condition interval after timezone offset
		# set up:
		self.timeCondition.timezone = localTimezone
		self.timeCondition.fromHour = 2
		self.timeCondition.fromMinute = 2
		self.timeCondition.toHour = 2
		self.timeCondition.toMinute = 15
		# tests:
		self.validateCondition("2018-10-05 02:01", False)
		self.validateCondition("2018-10-05 02:04", True)
		self.validateCondition("2018-10-05 02:16", False)

		# Test for other timezone in test system
		# set up:
		self.timeCondition.timezone = 'Europe/Stockholm'
		self.timeCondition.fromHour = 0
		self.timeCondition.fromMinute = 2
		self.timeCondition.toHour = 0
		self.timeCondition.toMinute = 15
		# tests:
		self.validateCondition("2018-10-05 22:01", False, True)  # note, this is in UTC
		self.validateCondition("2018-10-05 22:04", True, True)  # note, this is in UTC
		self.validateCondition("2018-10-05 22:16", False, True)  # note, this is in UTC

		# Tests when transitioning to DST
		# (2:00-3:00 does not exist)
		# set up:
		self.timeCondition.timezone = localTimezone
		self.timeCondition.fromHour = 2
		self.timeCondition.fromMinute = 2
		self.timeCondition.toHour = 2
		self.timeCondition.toMinute = 15
		# tests:
		self.validateCondition("2018-03-25 01:04", False)  # interval does not exist, literally
		self.validateCondition("2018-03-25 03:04", False)  # interval does not exist
		# set up:
		self.timeCondition.fromHour = 1
		self.timeCondition.fromMinute = 2
		self.timeCondition.toHour = 2  # to-time does not exist, is converted to 01.59
		self.timeCondition.toMinute = 15
		# tests:
		self.validateCondition("2018-03-25 01:05", True)
		self.validateCondition("2018-03-25 03:05", False)
		# set up:
		self.timeCondition.fromHour = 2  # from-time does not exist, is converted to 03:00
		self.timeCondition.fromMinute = 2
		self.timeCondition.toHour = 3
		self.timeCondition.toMinute = 15
		# tests:
		self.validateCondition("2018-03-25 01:06", False)
		self.validateCondition("2018-03-25 03:06", True)
		self.validateCondition("2018-03-25 03:16", False)
		# set up:
		self.timeCondition.fromHour = 1
		self.timeCondition.fromMinute = 2
		self.timeCondition.toHour = 3
		self.timeCondition.toMinute = 15
		# tests:
		self.validateCondition("2018-03-25 01:07", True)
		self.validateCondition("2018-03-25 03:07", True)
		# set up:
		self.timeCondition.fromHour = 22  # condition starts day before
		self.timeCondition.fromMinute = 10
		self.timeCondition.toHour = 2
		self.timeCondition.toMinute = 15
		# tests:
		# to-time should have been converted to 01:59, but is not, but the end result is correct:
		self.validateCondition("2018-03-24 23:07", True)
		# to-time converted to 01:59, which is really incorrect, but the end result is correct
		self.validateCondition("2018-03-25 23:08", True)
		self.validateCondition("2018-03-25 01:15", True)
		self.validateCondition("2018-03-25 03:02", False)
		# tests:
		self.timeCondition.fromHour = 2
		self.timeCondition.fromMinute = 10
		self.timeCondition.toHour = 5
		self.timeCondition.toMinute = 15
		# tests:
		self.validateCondition("2018-03-24 23:07", False)
		self.validateCondition("2018-03-25 23:08", False)
		self.validateCondition("2018-03-24 02:18", True)

		# Tests when leaving DST
		# (2:00-3:00 occurs twice)
		# set up, checking an interval occuring two times
		self.timeCondition.timezone = 'Europe/Stockholm'
		self.timeCondition.fromHour = 2
		self.timeCondition.fromMinute = 2
		self.timeCondition.toHour = 2
		self.timeCondition.toMinute = 15
		# tests:
		self.validateCondition("2018-10-28 00:04", True, True)
		self.validateCondition("2018-10-28 01:04", True, True)
		self.validateCondition("2018-10-28 00:01", False, True)
		self.validateCondition("2018-10-28 01:01", False, True)
		self.validateCondition("2018-10-28 00:10", True, True)
		self.validateCondition("2018-10-28 01:10", True, True)
		self.validateCondition("2018-10-28 00:16", False, True)
		self.validateCondition("2018-10-28 01:16", False, True)
		# set up:
		self.timeCondition.timezone = 'Europe/Stockholm'
		self.timeCondition.fromHour = 0
		self.timeCondition.fromMinute = 2
		self.timeCondition.toHour = 2
		self.timeCondition.toMinute = 15
		# tests:
		self.validateCondition("2018-10-28 23:04", True, True)
		self.validateCondition("2018-10-28 01:04", True, True)
		self.validateCondition("2018-10-28 02:16", False, True)
		self.validateCondition("2018-10-27 22:01", False, True)
		self.validateCondition("2018-10-27 22:02", True, True)
		self.validateCondition("2018-10-28 00:01", True, True)
		self.validateCondition("2018-10-28 01:01", True, True)
		self.validateCondition("2018-10-28 00:10", True, True)
		self.validateCondition("2018-10-28 01:10", True, True)
		self.validateCondition("2018-10-28 00:16", True, True)  # 01:16 OR 02:16 local time
		self.validateCondition("2018-10-28 01:16", False, True)
		# set up:
		self.timeCondition.timezone = 'Europe/Stockholm'
		self.timeCondition.fromHour = 2
		self.timeCondition.fromMinute = 2
		self.timeCondition.toHour = 5
		self.timeCondition.toMinute = 15
		# tests:
		self.validateCondition("2018-10-28 23:04", False, True)
		self.validateCondition("2018-10-28 02:16", True, True)
		self.validateCondition("2018-10-27 22:01", False, True)
		self.validateCondition("2018-10-27 22:02", False, True)
		self.validateCondition("2018-10-28 00:01", False, True)
		self.validateCondition("2018-10-28 01:01", True, True)
		self.validateCondition("2018-10-28 00:10", True, True)
		self.validateCondition("2018-10-28 01:10", True, True)
		self.validateCondition("2018-10-28 00:16", True, True)
		self.validateCondition("2018-10-28 01:16", True, True)
		# set up:
		self.timeCondition.timezone = localTimezone
		self.timeCondition.fromHour = 1
		self.timeCondition.fromMinute = 2
		self.timeCondition.toHour = 2
		self.timeCondition.toMinute = 15
		# tests:
		self.validateCondition("2018-10-28 00:05", False)
		self.validateCondition("2018-10-28 01:05", True)
		self.validateCondition("2018-10-28 02:05", True)
		self.validateCondition("2018-10-28 03:05", False)
		# set up:
		self.timeCondition.fromHour = 2
		self.timeCondition.fromMinute = 2
		self.timeCondition.toHour = 3
		self.timeCondition.toMinute = 15
		# tests:
		self.validateCondition("2018-10-28 01:06", False)
		self.validateCondition("2018-10-28 03:06", True)
		self.validateCondition("2018-10-28 03:16", False)
		# set up:
		self.timeCondition.fromHour = 1
		self.timeCondition.fromMinute = 2
		self.timeCondition.toHour = 3
		self.timeCondition.toMinute = 15
		# tests:
		self.validateCondition("2018-10-28 01:07", True)
		self.validateCondition("2018-10-28 03:07", True)
		# set up:
		self.timeCondition.fromHour = 22  # condition starts day before
		self.timeCondition.fromMinute = 10
		self.timeCondition.toHour = 2
		self.timeCondition.toMinute = 15
		# tests:
		self.validateCondition("2018-10-27 23:07", True)
		self.validateCondition("2018-10-28 23:08", True)
		self.validateCondition("2018-10-28 01:15", True)
		self.validateCondition("2018-10-28 02:15", True)
		self.validateCondition("2018-10-28 03:02", False)
		# set up:
		self.timeCondition.fromHour = 2
		self.timeCondition.fromMinute = 10
		self.timeCondition.toHour = 5
		self.timeCondition.toMinute = 15
		# tests:
		self.validateCondition("2018-10-27 23:07", False)
		self.validateCondition("2018-10-28 23:08", False)
		self.validateCondition("2018-10-27 02:18", True)

	def testBlockheaterTrigger(self):
		self.usertimezone = 'Europe/Stockholm'
		self.resetTrigger(timezone=self.usertimezone)

		with freeze_time(self.freezeTimeSimplifier("2018-10-01 05:00")):
			self.checkTime(6, 38)  # "ordinary" test
			self.blockHeaterTrigger.setTemp(-10)
			self.checkTime(6, 38)  # no change

		with freeze_time(self.freezeTimeSimplifier("2018-10-01 06:30")):
			self.blockHeaterTrigger.setTemp(-12)
			self.checkTime(6, 35)  # adjusted
			self.blockHeaterTrigger.setTemp(-20)
			# changed to something already passed, previous time is not altered
			# but call count should have increased
			self.checkTime(6, 24)
			self.assertTrue(self.blockHeaterTrigger.event.execute.call_count == 1)

		# Check that trigger isn't run when it has already triggered once
		self.blockHeaterTrigger.event.execute.reset_mock()
		with freeze_time(self.freezeTimeSimplifier("2018-10-02 05:00")):
			self.blockHeaterTrigger.setTemp(-12)  # 6:35
		with freeze_time(self.freezeTimeSimplifier("2018-10-02 06:35")):
			self.blockHeaterTrigger.manager.runMinute()
			self.assertTrue(self.blockHeaterTrigger.event.execute.call_count == 1)
			self.blockHeaterTrigger.manager.lastMinute = None  # bit of a cheat
			self.blockHeaterTrigger.manager.runMinute()
			self.assertTrue(self.blockHeaterTrigger.event.execute.call_count == 1)  # not run again (since removed)
			self.blockHeaterTrigger.setTemp(-12)  # 6:35
			self.blockHeaterTrigger.manager.lastMinute = None  # bit of a cheat
			self.blockHeaterTrigger.manager.runMinute()
			self.assertTrue(self.blockHeaterTrigger.event.execute.call_count == 1)
		with freeze_time(self.freezeTimeSimplifier("2018-10-03 06:35")):
			self.blockHeaterTrigger.manager.runMinute()
			self.assertTrue(self.blockHeaterTrigger.event.execute.call_count == 1)
			self.blockHeaterTrigger.manager.lastMinute = None  # bit of a cheat
			self.blockHeaterTrigger.setTemp(-12)  # 6:35
			self.blockHeaterTrigger.manager.runMinute()
			self.assertTrue(self.blockHeaterTrigger.event.execute.call_count == 2)
		with freeze_time(self.freezeTimeSimplifier("2018-10-03 06:38")):
			self.blockHeaterTrigger.manager.lastMinute = None  # bit of a cheat
			self.blockHeaterTrigger.setTemp(-10)  # 6:38
			self.blockHeaterTrigger.manager.runMinute()
			self.assertTrue(self.blockHeaterTrigger.event.execute.call_count == 2)

		self.resetTrigger(timezone=self.usertimezone)
		with freeze_time(self.freezeTimeSimplifier("2018-10-01 06:38")):
			# Check that time is pushed forward as temperature rises
			self.blockHeaterTrigger.setTemp(5)  # 07:17
			self.checkTime(7, 17)  # adjusted
			self.assertTrue(self.blockHeaterTrigger.event.execute.call_count == 0)

		with freeze_time(self.freezeTimeSimplifier("2018-10-01 06:34")):
			# test if triggered when using current value when reloading trigger
			self.resetTrigger(-12, timezone=self.usertimezone)
			self.assertTrue(self.blockHeaterTrigger.event.execute.call_count == 0)
			self.blockHeaterTrigger.manager.runMinute()
			self.assertTrue(self.blockHeaterTrigger.event.execute.call_count == 1)
			self.checkTime(6, 34)

		with freeze_time(self.freezeTimeSimplifier("2018-10-01 06:38")):
			# test if triggered when using current value when reloading trigger, already passed
			self.resetTrigger(-12, timezone=self.usertimezone)
			self.assertTrue(self.blockHeaterTrigger.event.execute.call_count == 1)
			self.blockHeaterTrigger.manager.runMinute()
			self.assertTrue(self.blockHeaterTrigger.event.execute.call_count == 1)
			self.checkTime(6, 34)

		with freeze_time(self.freezeTimeSimplifier("2018-10-01 05:00")):
			self.resetTrigger(-12, timezone=self.usertimezone)
			self.assertTrue(self.blockHeaterTrigger.event.execute.call_count == 0)
			self.blockHeaterTrigger.manager.runMinute()
			self.assertTrue(self.blockHeaterTrigger.event.execute.call_count == 0)
			self.checkTime(6, 34)

		with freeze_time(self.freezeTimeSimplifier("2018-10-01 05:00")):
			# test if trigger is inactivated if temperature rises above 10
			self.resetTrigger(-12, timezone=self.usertimezone)
			self.blockHeaterTrigger.manager.runMinute()
			self.assertTrue(self.blockHeaterTrigger.event.execute.call_count == 0)
			self.checkTime(6, 34)
			self.assertTrue(self.blockHeaterTrigger.active)
			self.blockHeaterTrigger.setTemp(11)
			self.blockHeaterTrigger.manager.runMinute()
			self.assertFalse(self.blockHeaterTrigger.active)
			# ...and then reactivates if lower temperature again
			self.blockHeaterTrigger.setTemp(-5)
			self.blockHeaterTrigger.manager.runMinute()
			self.checkTime(6, 48)
			self.assertTrue(self.blockHeaterTrigger.active)

		with freeze_time(self.freezeTimeSimplifier("2018-10-01 07:30")):
			# test if trigger is still active if temperature rises above 10 but
			# it's less than 2 hours until departure
			self.resetTrigger(9, timezone=self.usertimezone)
			self.blockHeaterTrigger.manager.runMinute()
			self.assertTrue(self.blockHeaterTrigger.event.execute.call_count == 0)
			self.checkTime(7, 35)
			self.assertTrue(self.blockHeaterTrigger.active)
			self.blockHeaterTrigger.setTemp(11)
			self.blockHeaterTrigger.manager.runMinute()
			self.assertTrue(self.blockHeaterTrigger.active)

		with freeze_time(self.freezeTimeSimplifier("2018-10-01 02:30")):
			# test that turn on-time is never set to more that 120 minutes before departure
			self.resetTrigger(9, timezone=self.usertimezone)
			self.blockHeaterTrigger.setTemp(-100)
			self.blockHeaterTrigger.manager.runMinute()
			self.checkTime(6, 0)

		with freeze_time(self.freezeTimeSimplifier("2018-10-01 07:30")):
			# make sure triggered is saved between server changes (trigger reloads)
			self.resetTrigger(5, timezone=self.usertimezone)
			self.blockHeaterTrigger.setTemp(-10)
			self.blockHeaterTrigger.manager.runMinute()
			self.checkTime(6, 38)
			firstId = id(self.blockHeaterTrigger)
			firstTriggeredAt = self.blockHeaterTrigger.triggeredAt
			kwargs = {'params': {'sensorId': '1000348', 'clientSensorId': 97, 'minute': '0', 'hour': '11'}, 'event': self.blockHeaterTrigger.event, 'id': 833}
			self.blockHeaterTrigger = ModifiedBlockheaterTrigger(self.usertimezone, self.blockHeaterTrigger.factory, self.blockHeaterTrigger.manager, self.blockHeaterTrigger.deviceManager, **kwargs)
			self.assertNotEqual(firstId, id(self.blockHeaterTrigger))
			self.assertEqual(firstTriggeredAt, self.blockHeaterTrigger.triggeredAt)

			# longitude, latitude or timezone changed
		with freeze_time(self.freezeTimeSimplifier("2018-10-01 07:35")):
			# make sure triggered is removed if timezone is updated
			# if parameters are parsed, it's always a new trigger, but
			# we don't know if it's something that has been changed or
			# just a server reload, so keep triggeredAt in that case
			self.resetTrigger(5, timezone=self.usertimezone)
			self.assertNotEqual(self.blockHeaterTrigger.triggeredAt, None)
			self.assertNotEqual(self.blockHeaterTrigger.manager.triggered, {})
			self.blockHeaterTrigger.timezone = 'Asia/Singapore'
			self.blockHeaterTrigger.manager.recalcAll()
			self.blockHeaterTrigger.timezone = self.usertimezone
			self.assertEqual(self.blockHeaterTrigger.triggeredAt, None)
			self.assertEqual(self.blockHeaterTrigger.manager.triggered, {})

		# midnight and timezone-tests:
		with freeze_time(self.freezeTimeSimplifier("2018-10-01 23:30")):
			# test incoming value before midnight
			self.resetTrigger(5, timezone=self.usertimezone)
			self.blockHeaterTrigger.parseParam('hour', 1)
			self.blockHeaterTrigger.parseParam('minute', 0)
			self.blockHeaterTrigger.manager.runMinute()
			self.checkTime(0, 17)

		with freeze_time(self.freezeTimeSimplifier("2018-10-02 01:30")):
			# test incoming value around midnight
			self.resetTrigger(5, timezone=self.usertimezone)
			self.blockHeaterTrigger.parseParam('hour', 3)
			self.blockHeaterTrigger.parseParam('minute', 0)
			self.blockHeaterTrigger.manager.runMinute()
			self.checkTime(2, 17)

		with freeze_time(pytz.timezone('UTC').localize( \
			   parser.parse("2018-10-01 23:30")).astimezone(pytz.utc)):
			# test incoming value before midnight, UTC
			self.resetTrigger(5, timezone='UTC')
			self.blockHeaterTrigger.parseParam('hour', 1)
			self.blockHeaterTrigger.parseParam('minute', 0)
			self.blockHeaterTrigger.manager.runMinute()
			self.checkTime(0, 17)

		with freeze_time(self.freezeTimeSimplifier("2018-10-01 08:01")):
			# just passed departure time
			self.resetTrigger(5, timezone=self.usertimezone)
			self.blockHeaterTrigger.parseParam('hour', 8)
			self.blockHeaterTrigger.parseParam('minute', 0)
			self.blockHeaterTrigger.manager.runMinute()
			# set for tomorrow (if no other values are received for the whole day, then this will actually be used)
			self.checkTime(7, 17)
			self.assertTrue(self.blockHeaterTrigger.event.execute.call_count == 0)

		with freeze_time(self.freezeTimeSimplifier("2018-10-01 08:00")):
			# at departure time!
			self.resetTrigger(5, timezone=self.usertimezone)
			self.blockHeaterTrigger.parseParam('hour', 8)
			self.blockHeaterTrigger.parseParam('minute', 0)
			self.blockHeaterTrigger.manager.runMinute()
			self.checkTime(7, 17)  # set for tomorrow (if no other values are received for the whole day, then this will actually be used)
			self.assertTrue(self.blockHeaterTrigger.event.execute.call_count == 0)

		with freeze_time(self.freezeTimeSimplifier("2018-10-01 07:59")):
			# 1 minute before departure time
			self.resetTrigger(5, timezone=self.usertimezone)
			self.blockHeaterTrigger.parseParam('hour', 8)
			self.blockHeaterTrigger.parseParam('minute', 0)
			self.blockHeaterTrigger.manager.runMinute()
			self.checkTime(7, 17)  # set for tomorrow (if no other values are received for the whole day, then this will actually be used)
			self.assertTrue(self.blockHeaterTrigger.event.execute.call_count == 1)

		with freeze_time(self.freezeTimeSimplifier("2018-10-01 05:00")):
			# check existing temp values not too old on load
			self.resetTrigger(0, timezone=self.usertimezone, lastUpdated=time.time())
			self.checkTime(7, 0)
			self.resetTrigger(10, timezone=self.usertimezone, lastUpdated=time.time()-7201)
			self.checkTime(None, None)  # too old
			self.resetTrigger(10, timezone=self.usertimezone, lastUpdated=time.time()-7199)
			self.checkTime(7, 40)

		with freeze_time(self.freezeTimeSimplifier("2018-10-01 15:00")):
			# check if already triggered today, that morethan2hourstodeparture is not negative
			self.resetTrigger(-5, timezone=self.usertimezone, lastUpdated=time.time())
			self.assertEqual(self.blockHeaterTrigger.moreThan2HoursToDeparture(), True)

		with freeze_time(self.freezeTimeSimplifier("2018-10-02 01:30")):
			# test incoming value before midnight, that morethan2hourstodeparture is still valid
			self.resetTrigger(9, timezone=self.usertimezone)
			self.blockHeaterTrigger.parseParam('hour', 3)
			self.blockHeaterTrigger.parseParam('minute', 0)
			self.assertEqual(self.blockHeaterTrigger.moreThan2HoursToDeparture(), False)

		with freeze_time(self.freezeTimeSimplifier("2018-10-02 07:00")):
			# test incoming value before midnight, that morethan2hourstodeparture is still valid
			self.resetTrigger(14, timezone=self.usertimezone)
			self.assertEqual(self.blockHeaterTrigger.setHour, None)
			self.assertEqual(self.blockHeaterTrigger.minute, None)
			self.resetTrigger(12, timezone=self.usertimezone)  # close to departure, 12 is OK
			self.assertEqual(self.blockHeaterTrigger.setHour, 7)
			self.assertEqual(self.blockHeaterTrigger.minute, 52)
			self.assertEqual(self.blockHeaterTrigger.active, True)
			self.blockHeaterTrigger.setTemp(14) # no change, but inactive...
			self.assertEqual(self.blockHeaterTrigger.active, False)
			self.assertEqual(self.blockHeaterTrigger.setHour, 7)
			self.assertEqual(self.blockHeaterTrigger.minute, 52)
			self.blockHeaterTrigger.setTemp(9)
			self.assertEqual(self.blockHeaterTrigger.active, True)

	def testTimeTrigger(self):
		self.usertimezone = 'Europe/Stockholm'
		with freeze_time(self.freezeTimeSimplifier("2018-10-01 05:05")):
			# check that everything is OK
			self.timeTrigger.parseParam('hour', 8)
			self.timeTrigger.parseParam('minute', 0)
			self.timeTrigger.manager.runMinute()
			self.assertTrue(self.timeTrigger.event.execute.call_count == 0)
		with freeze_time(self.freezeTimeSimplifier("2018-10-01 08:00")):
			# ordinary run
			self.timeTrigger.manager.runMinute()
			self.assertTrue(self.timeTrigger.event.execute.call_count == 1)
		with freeze_time(self.freezeTimeSimplifier("2018-10-01 08:00:01")):
			# don't run twice this minute, "isTriggered" prevents it
			self.timeTrigger.manager.lastMinute = None  # bit of a cheat, but want to test isTriggered
			self.timeTrigger.manager.runMinute()
			self.assertTrue(self.timeTrigger.event.execute.call_count == 1)
		with freeze_time(self.freezeTimeSimplifier("2018-10-01 08:00:02")):
			# don't run twice this minute, "lastMinute" prevents it (doesn't make it through trigger reloads)
			self.timeTrigger.manager.runMinute()
			self.assertTrue(self.timeTrigger.event.execute.call_count == 1)
			self.timeTrigger.parseParam('hour', 8)
			self.timeTrigger.parseParam('minute', 5)
		with freeze_time(self.freezeTimeSimplifier("2018-10-01 08:05:30")):
			# new time set, should run
			self.timeTrigger.manager.runMinute()
			self.assertTrue(self.timeTrigger.event.execute.call_count == 2)

