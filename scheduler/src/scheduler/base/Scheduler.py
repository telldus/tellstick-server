# -*- coding: utf-8 -*-
import copy
import random
import threading
import time
from base import Application, mainthread, Settings, Plugin, implements
from calendar import timegm
from collections import OrderedDict
from datetime import date, datetime, timedelta
from astral import Location
from pytz import timezone
from telldus import DeviceManager, Device
from tellduslive.base import TelldusLive, LiveMessage, ITelldusLiveObserver

class Scheduler(Plugin):
	implements(ITelldusLiveObserver)

	def __init__(self):
		self.running = False
		#self.runningJobsLock = threading.Lock()
		self.runningJobs = {} #id:s as keys
		self.s = Settings('telldus.scheduler')
		Application().registerShutdown(self.stop)
		self.fetchLocalJobs()
		self.live = TelldusLive(self.context)
		self.deviceManager = DeviceManager(self.context)
		if self.live.isRegistered():
			#probably not practically possible to end up here
			self.requestJobsFromServer()

		self.thread = threading.Thread(target=self.run)
		self.thread.start()

	def calculateJobs(self, jobs):
		"""Calculate nextRunTime for all jobs in the supplied list, order it and assign it to self.jobs"""
		for job in jobs:
			self.calculateNextRunTime(job)

		jobs.sort(key=lambda job: job['nextRunTime'])
		with self.jobsLock:
			self.jobs = jobs

	def calculateNextRunTime(self, job):
		"""Calculates nextRunTime for a job, depending on time, weekday and timezone."""
		if not job['active']:
			job['nextRunTime'] = 9999999999999 #todo, set to max or something
			return
		today = date.today().weekday()
		weekdays = [int(n) for n in job['weekdays'].split(',')]
		runToday = False
		firstWeekdayToRun = None
		nextWeekdayToRun = None
		runDate = None

		for weekday in weekdays:
			weekday = weekday - 1 #weekdays in python: 0-6, weekdays in our database: 1-7
			if weekday == today:
				runToday = True
			elif today < weekday and (nextWeekdayToRun is None or nextWeekdayToRun > weekday):
				nextWeekdayToRun = weekday
			elif today > weekday and (firstWeekdayToRun is None or weekday < firstWeekdayToRun):
				firstWeekdayToRun = weekday

		todayDate = date.today()
		if runToday:
			#this weekday is included in the ones that this schedule should be run on
			runTimeToday = self.calculateRunTimeForDay(todayDate, job)
			if runTimeToday > time.time():
				job['nextRunTime'] = runTimeToday + random.randint(0, job['random_interval'])
				return
			elif len(weekdays) == 1:
				#this job should only run on this weekday, since it has already passed today, run it next week
				runDate = todayDate + timedelta(days=7)

		if not runDate:
			if nextWeekdayToRun is not None:
				runDate = self.calculateNextWeekday(todayDate, nextWeekdayToRun)

			else:
				runDate = self.calculateNextWeekday(todayDate, firstWeekdayToRun)

			if not runDate:
				#something is wrong, no weekday to run
				job['active'] = False
				job['nextRunTime'] = 9999999999999 #todo, set to max or something
				print "Error" #TODO
				return

		job['nextRunTime'] = self.calculateRunTimeForDay(runDate, job) + random.randint(0, job['random_interval'])

	def calculateNextWeekday(self, d, weekday):
		days_ahead = weekday - d.weekday()
		if days_ahead <= 0: # Target day already happened this week
			days_ahead += 7
		return d + timedelta(days_ahead)

	def calculateRunTimeForDay(self, runDate, job):
		"""Calculates and returns a timestamp for when this job should be run next. Takes timezone into consideration."""
		runDate = datetime(runDate.year, runDate.month, runDate.day)
		if job['type'] == 'time':
			tt = timezone(self.timezone) #TODO, sending timezone from the server now, but it's really a client setting, can I get it from somewhere else?
			runDate = runDate + timedelta(hours=job['hour'], minutes=job['minute']) #won't random here, since this time may also be used to see if it's passed today or not
			return timegm(tt.localize(runDate).utctimetuple()) #returning a timestamp, corrected for timezone settings
		elif job['type'] == 'sunrise':
			#using astral, OK? At least smaller than PyEphem
			astralLocation = Location(("Client", "Local", float(self.latitude), float(self.longitude), self.timezone))
			runDate = astralLocation.sunrise(runDate)
			return timegm(runDate.utctimetuple()) + job['offset'] * 60 #returning a timestamp, corrected for timezone settings
		elif job['type'] == 'sunset':
			return timegm(Location(("Client", "Local", float(self.latitude), float(self.longitude), self.timezone)).sunset(runDate).utctimetuple()) + job['offset'] * 60

	def fetchLocalJobs(self):
		"""Fetch local jobs from settings"""
		try:
			jobs = self.s.get('jobs', [])
		except ValueError:
			jobs = [] #something bad has been stored, just ignore it and continue?
			print "WARNING: Could not fetch schedules from local storage"
		self.timezone = self.s.get('tz', 'UTC') #TODO all these should probably be fetched elsewhere?
		self.latitude = self.s.get('latitude', '55.699592')
		self.longitude = self.s.get('longitude', '13.187836')
		self.calculateJobs(jobs)

	def liveRegistered(self, msg):
		self.requestJobsFromServer()

	@TelldusLive.handler('scheduler-report')
	def receiveJobsFromServer(self, msg):
		"""Receive list of jobs from server, saves to settings and calculate nextRunTimes"""
		if len(msg.argument(0).toNative()) == 0:
			jobs = []
		else:
			scheduleDict = msg.argument(0).toNative()
			jobs = scheduleDict['jobs']
			self.timezone = scheduleDict['tz']
		self.s['jobs'] = jobs
		self.s['tz'] = self.timezone
		self.calculateJobs(jobs)

	def requestJobsFromServer(self):
		self.live.send(LiveMessage("scheduler-requestjob"))

	def run(self):
		self.running = True
		while self.running:
			#if len(self.jobs) > 0:
			#	print str(self.jobs[0]['nextRunTime']), " vs ", str(time.time())
			if len(self.jobs) > 0 and self.jobs[0]['nextRunTime'] < time.time():
				#a job has passed its nextRunTime
				job = self.jobs[0]
				jobId = job['id']
				#with self.runningJobsLock:
				jobCopy = copy.deepcopy(job) #make a copy, don't edit the original job
				jobCopy['originalRepeats'] = job['reps']
				jobCopy['maxRunTime'] = jobCopy['nextRunTime'] + jobCopy['reps'] * 3 + jobCopy['retry_interval'] * 60 * (jobCopy['retries'] + 1) + 70 + jobCopy['random_interval'] * 60 + jobCopy['offset'] * 60 #approximate maxRunTime, sanity check
				self.runningJobs[jobId] = jobCopy
				self.calculateNextRunTime(job)
				self.jobs.sort(key=lambda job: job['nextRunTime'])

				#Retries: 	- 433: Abort if it has been sent
							#  - ZWave: Abort if receiver sends ack
				#Repeats: 433 only
				#TODO When starting up, should we check if schedules are within retry interval and run them again if so? Or
				#aviod that, since it could lead to that a job is run several times?

			jobsToRun = [] #jobs to run in a separate list, to avoid deadlocks (necessary?)
			#with self.runningJobsLock: #or release it between each?
			for runningJobId in self.runningJobs.keys():
				runningJob = self.runningJobs[runningJobId]
				if runningJob['nextRunTime'] < time.time():
					if runningJob['maxRunTime'] > time.time():
						isZWaveDevice = False #TODO
						if not isZWaveDevice:
							runningJob['reps'] = int(runningJob['reps']) - 1
							if runningJob['reps'] > 0: #TODO? >=
								runningJob['nextRunTime'] = time.time() + 3
								jobsToRun.append(runningJob)
								continue

						if runningJob['retries'] > 1: #0 or 1?
							runningJob['nextRunTime'] = time.time() + (runningJob['retry_interval'] * 60)
							runningJob['retries'] = runningJob['retries'] - 1
							runningJob['reps'] = runningJob['originalRepeats']
							jobsToRun.append(runningJob)
							continue

					del self.runningJobs[runningJobId] #max run time passed or out of retries

			for jobToRun in jobsToRun:
				self.runJob(jobToRun)

			time.sleep(5) # TODO decide on a time

	def stop(self):
		self.running = False

	def successfulJobRun(self, jobId):
		"""Called when job run was considered successful (acked by Z-Wave or sent away from 433), repeats should still be run"""
		self.runningJobs['retries'] = 0

	@mainthread
	def runJob(self, jobData):
		#TODO, correct method, statevalue too, possible to send to 433 and callback-method on success
		print "IS RUNNING A JOB"
		device = self.deviceManager.device(jobData['client_device_id'])
		status, statevalue = device.state()
		if status == 1:
			device.command('turnoff')
		else:
			device.command('turnon')