# -*- coding: utf-8 -*-

import unittest
import pytz
from dateutil import parser
from freezegun import freeze_time
from mock import Mock
from tzlocal import get_localzone
from ..SchedulerEventFactory import TimeCondition

# run this with python -m unittest scheduler.base.tests in the tellstick.sh-shell

class SchedulerTest(unittest.TestCase):
	def __init__(self, *args, **kwargs):
		super(SchedulerTest, self).__init__(*args, **kwargs)
		kwargs = {'event': None, 'id': None, 'group': None}
		self.timeCondition = TimeCondition(**kwargs)

	def setUp(self):
		pass

	def tearDown(self):
		pass

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
