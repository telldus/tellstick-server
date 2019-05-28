# -*- coding: utf-8 -*-

import threading
import time

from calendar import timegm
from datetime import datetime, timedelta
from pytz import timezone
import pytz

from base import Application, implements, Plugin, Settings, slot, ISignalObserver
from events.base import IEventFactory, Condition, Trigger
from telldus import Device, DeviceManager

from .SunCalculator import SunCalculator

class TimeTriggerManager(object):
	def __init__(self, run=True):
		self.lastMinute = None
		self.running = False
		self.timeLock = threading.Lock()
		# TODO, the list below should be written to file
		self.triggered = {}  # keep track of when triggered between reloads
		self.triggers = {}
		Application(run).registerShutdown(self.stop)
		if run:
			self.thread = threading.Thread(target=self.run)
			self.thread.start()

	def addTrigger(self, trigger):
		with self.timeLock:
			if not trigger.minute in self.triggers:
				self.triggers[trigger.minute] = []
			self.triggers[trigger.minute].append(trigger)

	def clearAll(self):
		with self.timeLock:
			self.triggers = {}  # empty all running triggers

	def deleteTrigger(self, trigger):
		with self.timeLock:
			for minute in self.triggers:
				try:
					self.triggers[minute].remove(trigger)
				except Exception as __error:
					pass

	def recalcAll(self):
		# needs to recalc all triggers, for example longitude/latitude/timezone has changed
		# reset triggeredAt in this case
		triggersToRemove = {}
		for minute in self.triggers:
			for trigger in self.triggers[minute]:
				if trigger.recalculate():
					# trigger was updated (new minute), move it around
					trigger.triggeredAt = None
					del self.triggered[trigger.id]
					if minute not in triggersToRemove:
						triggersToRemove[minute] = []
					triggersToRemove[minute].append(trigger)

		with self.timeLock:
			for minute in triggersToRemove:
				for trigger in triggersToRemove[minute]:
					self.triggers[minute].remove(trigger)
					if trigger.minute not in self.triggers:
						self.triggers[trigger.minute] = []
					self.triggers[trigger.minute].append(trigger)

	def recalcOne(self, trigger):
		if trigger.recalculate():
			with self.timeLock:
				for minute in self.triggers:
					if trigger in self.triggers[minute]:
						self.triggers[minute].remove(trigger)
				if trigger.minute not in self.triggers:
					self.triggers[trigger.minute] = []
				self.triggers[trigger.minute].append(trigger)

	def run(self):
		self.running = True
		self.lastMinute = None
		while self.running:
			self.runMinute()
			time.sleep(5)

	def runMinute(self):
		currentMinute = datetime.utcnow().minute
		if self.lastMinute is None or self.lastMinute is not currentMinute:
			# new minute, check triggers
			self.lastMinute = currentMinute
			if currentMinute not in self.triggers:
				return
			triggersToRemove = []
			for trigger in self.triggers[currentMinute]:
				if trigger.hour == -1 or trigger.hour == datetime.utcnow().hour:
					triggertype = 'time'
					if isinstance(trigger, SuntimeTrigger):
						triggertype = 'suntime'
					elif isinstance(trigger, BlockheaterTrigger):
						triggertype = 'blockheater'
					if isinstance(trigger, SuntimeTrigger) and trigger.recalculate():
						# suntime (time or active-status) was updated (new minute), move it around
						triggersToRemove.append(trigger)
					if trigger.active and not trigger.isTriggered():
						# is active (not inactive due to sunrise/sunset-thing)
						trigger.triggered({'triggertype': triggertype})
			with self.timeLock:
				for trigger in triggersToRemove:
					self.triggers[currentMinute].remove(trigger)
					if not trigger.active:
						continue
					if trigger.minute not in self.triggers:
						self.triggers[trigger.minute] = []
					self.triggers[trigger.minute].append(trigger)

	def stop(self):
		self.running = False

class TimeTrigger(Trigger):
	def __init__(self, manager, **kwargs):
		super(TimeTrigger, self).__init__(**kwargs)
		self.manager = manager
		self.calculatedTime = None
		self.minute = None
		self.hour = None
		self.setHour = None  # this is the hour actually set (not recalculated to UTC)
		self.active = True  # TimeTriggers are always active
		self.timezone = self.getTimezone()
		self.triggeredAt = self.fetchTriggeredAt()

	def close(self):
		self.manager.deleteTrigger(self)

	def fetchTriggeredAt(self):
		if self.id in self.manager.triggered:
			return  self.manager.triggered[self.id]
		return None

	def getSettings(self):
		return Settings('telldus.scheduler')

	def getTimezone(self):
		return self.getSettings().get('tz', 'UTC')

	def isTriggered(self):
		# is it already triggered this minute
		if self.triggeredAt:
			# note, nanosecond in the future?
			return datetime.fromtimestamp(self.triggeredAt).replace(second=0,
			   microsecond=0) == datetime.now().replace(second=0, microsecond=0)
		return False

	def parseParam(self, name, value):
		if name == 'minute':
			self.minute = int(value)
		elif name == 'hour':
			self.setHour = int(value)
			# recalculate hour to UTC
			if int(value) == -1:
				self.hour = int(value)
			else:
				local_timezone = timezone(self.timezone)
				currentDate = pytz.utc.localize(datetime.utcnow())
				local_datetime = local_timezone.localize(
					datetime(currentDate.year, currentDate.month, currentDate.day, int(value))
				)
				utc_datetime = pytz.utc.normalize(local_datetime.astimezone(pytz.utc))
				if datetime.now().hour > utc_datetime.hour:
					# retry it with new date (will have impact on daylight savings changes (but not
					# sure it will actually help))
					currentDate = currentDate + timedelta(days=1)
				local_datetime = local_timezone.localize(
					datetime(currentDate.year, currentDate.month, currentDate.day, int(value))
				)
				utc_datetime = pytz.utc.normalize(local_datetime.astimezone(pytz.utc))
				self.hour = utc_datetime.hour
		if self.hour is not None and self.minute is not None:
			self.manager.addTrigger(self)

	def recalculate(self):
		if self.hour == -1:
			return False
		currentHour = self.hour
		local_timezone = timezone(self.timezone)
		currentDate = pytz.utc.localize(datetime.utcnow())
		local_datetime = local_timezone.localize(
			datetime(currentDate.year, currentDate.month, currentDate.day, self.setHour)
		)
		utc_datetime = pytz.utc.normalize(local_datetime.astimezone(pytz.utc))
		if datetime.now().hour > utc_datetime.hour:
			# retry it with new date (will have impact on daylight savings changes (but not sure it
			# will actually help))
			currentDate = currentDate + timedelta(days=1)
			local_datetime = local_timezone.localize(
				datetime(currentDate.year, currentDate.month, currentDate.day, self.setHour)
			)
			utc_datetime = pytz.utc.normalize(local_datetime.astimezone(pytz.utc))
		self.hour = utc_datetime.hour
		self.calculatedHourTime = utc_datetime
		if currentHour == self.hour:
			#no change
			return False
		return True

	def triggered(self, triggerInfo=None):
		self.triggeredAt = time.time()
		self.manager.triggered[self.id] = self.triggeredAt
		super(TimeTrigger, self).triggered(triggerInfo)

class SuntimeTrigger(TimeTrigger):
	def __init__(self, manager, **kwargs):
		super(SuntimeTrigger, self).__init__(manager=manager, **kwargs)
		self.sunStatus = None
		self.offset = None
		self.latitude = self.getSettings().get('latitude', '55.699592')
		self.longitude = self.getSettings().get('longitude', '13.187836')

	def parseParam(self, name, value):
		if name == 'sunStatus':
			# rise = 1, set = 0
			self.sunStatus = int(value)
		elif name == 'offset':
			self.offset = int(value)
		if self.sunStatus is not None and self.offset is not None:
			self.recalculate()
			self.manager.addTrigger(self)

	def recalculate(self):
		self.latitude = self.getSettings().get('latitude', '55.699592')
		self.longitude = self.getSettings().get('longitude', '13.187836')
		sunCalc = SunCalculator()
		currentHour = self.hour
		currentMinute = self.minute
		currentDate = pytz.utc.localize(datetime.utcnow())
		riseSet = sunCalc.nextRiseSet(
			timegm(currentDate.utctimetuple()),
			float(self.latitude),
			float(self.longitude)
		)
		if self.sunStatus == 0:
			runTime = riseSet['sunset']
		else:
			runTime = riseSet['sunrise']
		runTime = runTime + (self.offset*60)
		utc_datetime = datetime.utcfromtimestamp(runTime)

		tomorrow = currentDate + timedelta(days=1)
		if (utc_datetime.day != currentDate.day or utc_datetime.month != currentDate.month) \
		   and (utc_datetime.day != tomorrow.day or utc_datetime.month != tomorrow.month):
			# no sunrise/sunset today or tomorrow
			if self.active:
				self.active = False
				return True  # has changed (status to active)
			return False  # still not active, no change
		if currentMinute == utc_datetime.minute and currentHour == utc_datetime.hour and self.active:
			return False  # no changes
		self.active = True
		self.minute = utc_datetime.minute
		self.hour = utc_datetime.hour
		return True

class BlockheaterTrigger(TimeTrigger):
	def __init__(self, factory, manager, deviceManager, **kwargs):
		super(BlockheaterTrigger, self).__init__(manager=manager, **kwargs)
		self.maxRunTime = 7200
		self.factory = factory
		self.departureHour = None
		self.departureMinute = None
		self.sensorId = None
		self.temp = None
		self.deviceManager = deviceManager

	def close(self):
		self.factory.deleteTrigger(self)
		super(BlockheaterTrigger, self).close()

	def isTriggered(self):
		# is it already triggered less than 2 hours ago?
		return (self.triggeredAt and self.triggeredAt > (time.time() - self.maxRunTime))

	def moreThan2HoursToDeparture(self):
		# even if the temperature rises above 10, don't inactivate the trigger
		# if it's less than 2 hours until departure
		if not self.active:
			return True
		local_timezone = timezone(self.timezone)
		currentDate = pytz.utc.localize(datetime.utcnow())
		local_datetime = local_timezone.localize(
			datetime(currentDate.year, currentDate.month, currentDate.day, self.departureHour, self.departureMinute)
		)
		utc_datetime = pytz.utc.normalize(local_datetime.astimezone(pytz.utc))
		if currentDate > utc_datetime:
			# departure time already passed today
			local_datetime = local_timezone.localize(
				datetime(currentDate.year, currentDate.month, currentDate.day+1, self.departureHour, self.departureMinute)
			)
			utc_datetime = pytz.utc.normalize(local_datetime.astimezone(pytz.utc))
		return currentDate < (utc_datetime - timedelta(hours=self.maxRunTime/3600))

	def parseParam(self, name, value):
		if name == 'clientSensorId':
			self.sensorId = int(value)
		elif name == 'hour':
			self.departureHour = int(value)
		elif name == 'minute':
			self.departureMinute = int(value)
		if self.departureHour is not None \
		   and self.departureMinute is not None \
		   and self.sensorId is not None:
			self.recalculate()
			self.manager.addTrigger(self)

	def recalculate(self):
		if self.temp is None:
			if self.sensorId is None:
				return False
			sensor = self.deviceManager.device(self.sensorId)
			# TODO: Support Fahrenheit also
			sensorElement = sensor.sensorElement(Device.TEMPERATURE, Device.SCALE_TEMPERATURE_CELCIUS)
			temp = sensorElement['value']
			if temp is None:
				return False
			if sensorElement['lastUpdated'] and sensorElement['lastUpdated'] < (time.time() - self.maxRunTime):
				# this fetched value was received too long ago, don't use this to set the blockheater
				return False
			self.temp = temp
		if (self.temp > 10 and self.moreThan2HoursToDeparture()) or self.temp > 13:
			self.active = False
			return True
		self.active = True
		offset = int(round(60+100*self.temp/(self.temp-35)))
		offset = min(self.maxRunTime/60, offset) #  Never longer than 120 minutes
		minutes = (self.departureHour * 60) + self.departureMinute - offset
		if minutes < 0:
			minutes += 24*60
		self.setHour = int(minutes / 60)
		minuteBefore = self.minute
		self.minute = int(minutes % 60)
		shouldRecalc = super(BlockheaterTrigger, self).recalculate() or minuteBefore != self.minute
		if self.calculatedHourTime and time.mktime(self.calculatedHourTime.replace(minute=self.minute).timetuple()) < time.time():
			# note, python 3 has .timestamp()
			# the new calculated value has already passed, run it now!
			if not self.isTriggered():
				self.triggered({'triggertype': 'blockheater'})
				return True
		return shouldRecalc

	def setTemp(self, temp):
		self.temp = temp
		self.manager.recalcOne(self)

class SuntimeCondition(Condition):
	def __init__(self, **kwargs):
		super(SuntimeCondition, self).__init__(**kwargs)
		self.sunStatus = None
		self.sunriseOffset = None
		self.sunsetOffset = None
		self.settings = self.getSettings()
		self.latitude = self.settings.get('latitude', '55.699592')
		self.longitude = self.settings.get('longitude', '13.187836')

	def parseParam(self, name, value):
		if name == 'sunStatus':
			self.sunStatus = int(value)
		if name == 'sunriseOffset':
			self.sunriseOffset = int(value)
		if name == 'sunsetOffset':
			self.sunsetOffset = int(value)

	def validate(self, success, failure):
		if self.sunStatus is None or self.sunriseOffset is None or self.sunsetOffset is None:
			# condition has not finished loading, impossible to validate it correctly
			failure()
			return
		sunCalc = SunCalculator()
		currentDate = pytz.utc.localize(datetime.utcnow())
		riseSet = sunCalc.nextRiseSet(
			timegm(currentDate.utctimetuple()),
			float(self.latitude),
			float(self.longitude)
		)
		currentStatus = 1
		sunToday = sunCalc.riseset(
			timegm(currentDate.utctimetuple()),
			float(self.latitude),
			float(self.longitude)
		)
		sunRise = None
		sunSet = None
		if sunToday['sunrise']:
			sunRise = sunToday['sunrise'] + (self.sunriseOffset*60)
		if sunToday['sunset']:
			sunSet = sunToday['sunset'] + (self.sunsetOffset*60)
		if sunRise or sunSet:
			if (sunRise and time.time() < sunRise) or (sunSet and time.time() > sunSet):
				currentStatus = 0
		else:
			# no sunset or sunrise, is it winter or summer?
			if riseSet['sunrise'] < riseSet['sunset']:
				# next is a sunrise, it's dark now (winter)
				if time.time() < (riseSet['sunrise'] + (self.sunriseOffset*60)):
					currentStatus = 0
			else:
				# next is a sunset, it's light now (summer)
				if time.time() > (riseSet['sunset'] + (self.sunriseOffset*60)):
					currentStatus = 0
		if self.sunStatus == currentStatus:
			success()
		else:
			failure()

class TimeCondition(Condition):
	def __init__(self, **kwargs):
		super(TimeCondition, self).__init__(**kwargs)
		self.fromMinute = None
		self.fromHour = None
		self.toMinute = None
		self.toHour = None
		self.timezone = self.getTimezone()

	def parseParam(self, name, value):
		if name == 'fromMinute':
			self.fromMinute = int(value)
		elif name == 'toMinute':
			self.toMinute = int(value)
		elif name == 'fromHour':
			self.fromHour = int(value)
		elif name == 'toHour':
			self.toHour = int(value)

	def validate(self, success, failure):
		utcCurrentDate = pytz.utc.localize(datetime.utcnow())
		local_timezone = timezone(self.timezone)
		currentDate = utcCurrentDate.astimezone(local_timezone)

		if self.fromMinute is None \
		   or self.toMinute is None \
		   or self.fromHour is None \
		   or self.toHour is None:
			# validate that all parameters have been loaded
			failure()
			return
		fromTimeNonExistent = False
		fromTimeIsAmbigious = False
		try:
			fromTime = local_timezone.localize(
				datetime(
					currentDate.year, currentDate.month, currentDate.day, self.fromHour, self.fromMinute, 0
				), is_dst=None
			)
		except pytz.exceptions.NonExistentTimeError:
			# we reckon this has to be DST transition
			# since the condition starts at non-existing time, instead start it just after the DST switch
			fromTime = local_timezone.localize(
				datetime(currentDate.year, currentDate.month, currentDate.day, self.fromHour+1, 0, 0)
			)
			fromTimeNonExistent = True
		except pytz.exceptions.AmbiguousTimeError:
			fromTime = local_timezone.localize(
				datetime(
					currentDate.year, currentDate.month, currentDate.day, self.fromHour, self.fromMinute, 0
				), is_dst=True
			)
			fromTimeIsAmbigious = True
		try:
			toTime = local_timezone.localize(
				datetime(currentDate.year, currentDate.month, currentDate.day, self.toHour, self.toMinute, 0),
				is_dst=None
			)
		except pytz.exceptions.NonExistentTimeError:
			# we reckon this has to be DST transition
			# since the condition ends at non-existing time, instead end it just before the DST switch
			if fromTimeNonExistent:
				# in the condition interval, both from and to occurs in an non-existent time,
				# it can't fail much more than that
				failure()
				return
			toTime = local_timezone.localize(
				datetime(currentDate.year, currentDate.month, currentDate.day, self.toHour-1, 59, 59)
			)
		except pytz.exceptions.AmbiguousTimeError:
			if fromTimeIsAmbigious:
				# both to and from occurs in an ambigious time interval,
				# we have to check the condition against two intervals
				toTime = local_timezone.localize(
					datetime(currentDate.year, currentDate.month, currentDate.day, self.toHour, self.toMinute, 0),
					is_dst=True
				)
				if self.validateCompare(currentDate, toTime, fromTime):  # running compare for first interval
					success()
					return
				# first interval did not match, setting up for next interval:
				fromTime = local_timezone.localize(
					datetime(
						currentDate.year, currentDate.month, currentDate.day, self.fromHour, self.fromMinute, 0
					), is_dst=False
				)

			toTime = local_timezone.localize(
				datetime(currentDate.year, currentDate.month, currentDate.day, self.toHour, self.toMinute, 0),
				is_dst=False
			)
		if self.validateCompare(currentDate, toTime, fromTime):
			success()
		else:
			failure()

	@staticmethod
	def validateCompare(currentDate, toTime, fromTime):
		if fromTime > toTime:
			# condition interval passes midnight
			return (currentDate >= fromTime or currentDate <= toTime)
		return (currentDate >= fromTime and currentDate <= toTime)

class WeekdayCondition(Condition):
	def __init__(self, **kwargs):
		super(WeekdayCondition, self).__init__(**kwargs)
		self.weekdays = None
		self.timezone = self.getTimezone()

	def parseParam(self, name, value):
		if name == 'weekdays':
			self.weekdays = value

	def validate(self, success, failure):
		currentDate = pytz.utc.localize(datetime.utcnow())
		local_timezone = timezone(self.timezone)
		local_datetime = local_timezone.normalize(currentDate.astimezone(local_timezone))
		currentWeekday = local_datetime.weekday() + 1
		if str(currentWeekday) in self.weekdays:
			success()
		else:
			failure()

class SchedulerEventFactory(Plugin):
	implements(IEventFactory)
	implements(ISignalObserver)

	def __init__(self):
		self.triggerManager = TimeTriggerManager()
		self.blockheaterTriggers = []

	def clearAll(self):
		self.triggerManager.clearAll()

	@staticmethod
	def createCondition(type, params, **kwargs):  # pylint: disable=W0622
		del params
		if type == 'suntime':
			return SuntimeCondition(**kwargs)
		elif type == 'time':
			return TimeCondition(**kwargs)
		elif type == 'weekdays':
			return WeekdayCondition(**kwargs)

	def createTrigger(self, type, **kwargs):  # pylint: disable=W0622
		if type == 'blockheater':
			trigger = BlockheaterTrigger(
				factory=self,
				manager=self.triggerManager,
				deviceManager=DeviceManager(self.context),
				**kwargs
			)
			self.blockheaterTriggers.append(trigger)
			return trigger
		if type == 'time':
			return TimeTrigger(manager=self.triggerManager, **kwargs)
		if type == 'suntime':
			return SuntimeTrigger(manager=self.triggerManager, **kwargs)
		return None

	def deleteTrigger(self, trigger):
		if trigger in self.blockheaterTriggers:
			self.blockheaterTriggers.remove(trigger)

	def recalcTrigger(self):
		self.triggerManager.recalcAll()

	@slot('sensorValueUpdated')
	def sensorValueUpdated(self, device, valueType, value, __scale):
		if valueType != Device.TEMPERATURE:
			return
		for trigger in self.blockheaterTriggers:
			if trigger.sensorId == device.id():
				trigger.setTemp(value)
				break
