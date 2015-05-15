# -*- coding: utf-8 -*-

from base import Application, implements, Plugin, Settings
from calendar import timegm
from datetime import date, datetime, timedelta
from events.base import IEventFactory, Action, Condition, Trigger
from pytz import timezone
from SunCalculator import SunCalculator
import pytz
import threading
import time

class TimeTriggerManager(object):
	def __init__(self):
		self.running = False
		self.timeLock = threading.Lock()
		self.triggers = {}
		Application().registerShutdown(self.stop)
		self.thread = threading.Thread(target=self.run)
		self.thread.start()

	def addTrigger(self, trigger):
		with self.timeLock:
			if not trigger.minute in self.triggers:
				self.triggers[trigger.minute] = []
			self.triggers[trigger.minute].append(trigger)

	def run(self):
		self.running = True
		self.lastMinute = None
		while self.running:
			currentMinute = datetime.utcnow().minute
			if self.lastMinute is None or self.lastMinute is not currentMinute:
				# new minute, check triggers
				self.lastMinute = currentMinute
				if currentMinute not in self.triggers:
					continue
				triggersToRemove = []
				for trigger in self.triggers[currentMinute]:
					if trigger.hour == -1 or trigger.hour == datetime.utcnow().hour:
						if trigger.recalculate():
							# suntime (time or active-status) was updated (new minute), move it around
							triggersToRemove.append(trigger)
						if trigger.active:
							# is active (not inactive due to sunrise/sunset-thing)
							trigger.triggered()
				with self.timeLock:
					for trigger in triggersToRemove:
						self.triggers[currentMinute].remove(trigger)
						if not trigger.active:
							continue
						if trigger.minute not in self.triggers:
							self.triggers[trigger.minute] = []
						self.triggers[trigger.minute].append(trigger)
			time.sleep(5)

	def stop(self):
		self.running = False

class TimeTrigger(Trigger):
	def __init__(self, manager, **kwargs):
		super(TimeTrigger,self).__init__(**kwargs)
		self.manager = manager
		self.minute = None
		self.hour = None
		self.active = True  # TimeTriggers are always active
		self.s = Settings('telldus.scheduler')
		self.timezone = self.s.get('tz', 'UTC')

	def parseParam(self, name, value):
		if name == 'minute':
			self.minute = int(value)
		elif name == 'hour':
			# recalculate hour to UTC
			if int(value) == -1:
				self.hour = int(value)
			else:
				local_timezone = timezone(self.timezone)
				currentDate = pytz.utc.localize(datetime.utcnow())
				local_datetime = local_timezone.localize(datetime(currentDate.year, currentDate.month, currentDate.day, int(value)))
				utc_datetime = pytz.utc.normalize(local_datetime.astimezone(pytz.utc))
				if datetime.now().hour > utc_datetime.hour:
					# retry it with new date (will have impact on daylight savings changes (but not sure it will actually help))
					currentDate = currentDate + timedelta(days=1)
				local_datetime = local_timezone.localize(datetime(currentDate.year, currentDate.month, currentDate.day, int(value)))
				utc_datetime = pytz.utc.normalize(local_datetime.astimezone(pytz.utc))
				self.hour = utc_datetime.hour
		if self.hour is not None and self.minute is not None:
			self.manager.addTrigger(self)

	def recalculate(self):
		return False  # no need to recalculate anything

class SuntimeTrigger(TimeTrigger):
	def __init__(self, manager, **kwargs):
		super(SuntimeTrigger,self).__init__(manager = manager, **kwargs)
		self.sunStatus = None
		self.offset = None
		self.latitude = self.s.get('latitude', '55.699592')
		self.longitude = self.s.get('longitude', '13.187836')

	def parseParam(self, name, value):
		if name == 'sunStatus':
			# rise = 1, set = 0
			self.sunStatus = int(value)
		elif name == 'offset':
			self.offset = int(value)
		if self.sunStatus and self.offset is not None:
			self.recalculate()
			self.manager.addTrigger(self)

	def recalculate(self):
		sunCalc = SunCalculator()
		currentHour = self.hour 
		currentMinute = self.minute
		currentDate = pytz.utc.localize(datetime.utcnow())
		riseSet = sunCalc.nextRiseSet(timegm(currentDate.utctimetuple()), float(self.latitude), float(self.longitude))
		if self.sunStatus == 0:
			runTime = riseSet['sunset']
		else:
			runTime = riseSet['sunrise']
		runTime = runTime + (self.offset*60)
		utc_datetime = datetime.utcfromtimestamp(runTime)

		tomorrow = currentDate + timedelta(days=1)
		if (utc_datetime.day != currentDate.day or utc_datetime.month != currentDate.month) and (utc_datetime.day != tomorrow.day or utc_datetime.month != tomorrow.month):
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

class TimeCondition(Condition):
	def __init__(self, **kwargs):
		super(TimeCondition,self).__init__(**kwargs)
		self.fromMinute = None
		self.fromHour = None
		self.toMinute = None
		self.toHour = None
		self.s = Settings('telldus.scheduler')
		self.timezone = self.s.get('tz', 'UTC')

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
		currentDate = pytz.utc.localize(datetime.utcnow())
		local_timezone = timezone(self.timezone)

		if not self.fromMinute or not self.toMinute or not self.fromHour or not self.toHour:
			# validate that all parameters have been loaded
			failure()
		toTime = local_timezone.localize(datetime(currentDate.year, currentDate.month, currentDate.day, self.toHour, self.toMinute, 0))
		fromTime = local_timezone.localize(datetime(currentDate.year, currentDate.month, currentDate.day, self.fromHour, self.fromMinute, 0))
		if fromTime < toTime:
			# condition interval passes midnight
			if (currentDate >= fromTime and currentDate <= toTime):
				success()
			else:
				failure()
		else:
			if (currentDate >= fromTime or currentDate <= toTime):
				success()
			else:
				failure()

class WeekdayCondition(Condition):
	def __init__(self, **kwargs):
		super(WeekdayCondition,self).__init__(**kwargs)
		self.weekdays = None
		self.s = Settings('telldus.scheduler')
		self.timezone = self.s.get('tz', 'UTC')

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

	def __init__(self):
		self.triggerManager = TimeTriggerManager()

	def createCondition(self, type, params, **kwargs):
		if type == 'time':
			return TimeCondition(**kwargs)
		elif type == 'weekdays':
			return WeekdayCondition(**kwargs)

	def createTrigger(self, type, **kwargs):
		if type == 'time':
			trigger = TimeTrigger(manager=self.triggerManager, **kwargs)
			return trigger
		if type == 'suntime':
			trigger = SuntimeTrigger(manager=self.triggerManager, **kwargs)
			return trigger
		return None
