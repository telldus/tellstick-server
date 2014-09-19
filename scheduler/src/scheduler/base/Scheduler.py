# -*- coding: utf-8 -*-
import copy
import random
import threading
import time
from base import Application, mainthread, Settings, Plugin, implements
from calendar import timegm
from collections import OrderedDict
from datetime import date, datetime, timedelta
from pytz import timezone
from SunCalculator import SunCalculator
from telldus import DeviceManager, Device
from tellduslive.base import TelldusLive, LiveMessage, ITelldusLiveObserver

class Scheduler(Plugin):
	implements(ITelldusLiveObserver)

	def __init__(self):
		self.running = False
		#self.runningJobsLock = threading.Lock() #TODO needed?
		self.jobsLock = threading.Lock()
		self.runningJobs = {} #id:s as keys
		self.s = Settings('telldus.scheduler')
		Application().registerShutdown(self.stop)
		self.jobs = []
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
		newJobs = []
		for job in jobs:
			self.checkNewlyLoadedJob(job)
			if self.calculateNextRunTime(job):
				newJobs.append(job)

		newJobs.sort(key=lambda job: job['nextRunTime'])
		with self.jobsLock:
			self.jobs = newJobs

	def calculateNextRunTime(self, job):
		"""Calculates nextRunTime for a job, depending on time, weekday and timezone."""
		if not job['active']:
			job['nextRunTime'] = 253402214400 #set to max value, only run just before the end of time
			self.deleteJob(job['id'])	#just delete the job, until it's possible to edit schedules locally, inactive jobs has no place at all here
			return False
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
				job['nextRunTime'] = runTimeToday + random.randint(0, job['random_interval']) * 60
				return True
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
				job['nextRunTime'] = 253402214400
				self.deleteJob(job['id'])	#just delete the job, until it's possible to edit schedules locally, inactive jobs has no place at all here
				return False

		job['nextRunTime'] = self.calculateRunTimeForDay(runDate, job) + random.randint(0, job['random_interval']) * 60
		return True
		
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
			sunCalc = SunCalculator()
			riseSet = sunCalc.nextRiseSet(timegm(runDate.utctimetuple()), float(self.latitude), float(self.longitude))
			return riseSet['sunrise'] + job['offset'] * 60	
		elif job['type'] == 'sunset':
			sunCalc = SunCalculator()
			riseSet = sunCalc.nextRiseSet(timegm(runDate.utctimetuple()), float(self.latitude), float(self.longitude))
			return riseSet['sunset'] + job['offset'] * 60

	def checkNewlyLoadedJob(self, job):
		"""Checks if any of the jobs (local or initially loaded) should be running right now"""
		if not job['active']:
			return

		weekdays = [int(n) for n in job['weekdays'].split(',')]
		i = 0
		while i < 2:
			#Check today and yesterday (might be around 12 in the evening)
			currentDate = date.today() + timedelta(days=-i)
			if (currentDate.weekday() + 1) in weekdays:
				#check for this day (today or yesterday)
				runTime = self.calculateRunTimeForDay(currentDate, job)
				runTimeMax = runTime + job['reps'] * 3 + job['retry_interval'] * 60 * (job['retries'] + 1) + 70 + job['random_interval'] * 60 + job['offset'] * 60
				jobId = job['id']
				executedJobs = self.s.get('executedJobs', {})
				if (str(jobId) not in executedJobs or executedJobs[str(jobId)] < runTime) and  time.time() > runTime and time.time() < runTimeMax:
					#run time for this job was passed during downtime, but it was passed within the max-runtime, and the last time it was executed (successfully) was before this run time, so it should be run again...
					jobCopy = copy.deepcopy(job)
					jobCopy['originalRepeats'] = job['reps']
					jobCopy['nextRunTime'] = runTime
					jobCopy['maxRunTime'] = runTimeMax #approximate maxRunTime, sanity check
					self.runningJobs[jobId] = jobCopy
					return
			i = i + 1

	def deleteJob(self, jobId):
		with self.jobsLock:
			self.jobs[:] = [x for x in self.jobs if x['id'] != jobId] #Test this! It should be fast and keep original reference, they say (though it will iterate all, even if it could end after one)
			if jobId in self.runningJobs:	#TODO this might require a lock too?
				self.runningJobs[jobId]['retries'] = 0

			executedJobs = self.s.get('executedJobs', {})
			if str(jobId) in executedJobs:
				del executedJobs[str(jobId)]
				self.s['executedJobs'] = executedJobs

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

	@TelldusLive.handler('scheduler-update')
	def receiveOneJobFromServer(self, msg):
		"""Receive one job from server, add or edit, save to settings and calculate nextRunTime"""
		if len(msg.argument(0).toNative()) == 0:
			jobs = []
		else:
			scheduleDict = msg.argument(0).toNative()
			job = scheduleDict['job']
			self.timezone = scheduleDict['tz']

		self.s['tz'] = self.timezone
		active = self.calculateNextRunTime(job)
		self.deleteJob(job['id']) #delete the job if it already exists (update)
		if active:
			with self.jobsLock:
				self.jobs.append(job)
				self.jobs.sort(key=lambda job: job['nextRunTime'])
		self.s['jobs'] = self.jobs #save to storage
		#self.live.pushToWeb('scheduler', 'updated', job['id']) #TODO is this a good idea? Trying to avoid cache problems where updates haven't come through? But this may not work if the same schedule is saved many times in a row, or if changes wasn't saved correctly to the database (not possible yet, only one database for schedules)

	def requestJobsFromServer(self):
		self.live.send(LiveMessage("scheduler-requestjob"))

	def run(self):
		self.running = True
		time.sleep(10) #TODO have to have devices initiated before starting this (since we load schedules that should have been run during off)
		while self.running:
			jobCopy = None
			with self.jobsLock:
				if len(self.jobs) > 0 and self.jobs[0]['nextRunTime'] < time.time():
					#a job has passed its nextRunTime
					job = self.jobs[0]
					jobId = job['id']
					jobCopy = copy.deepcopy(job) #make a copy, don't edit the original job

			if jobCopy:
				jobCopy['originalRepeats'] = job['reps']
				jobCopy['maxRunTime'] = jobCopy['nextRunTime'] + jobCopy['reps'] * 3 + jobCopy['retry_interval'] * 60 * (jobCopy['retries'] + 1) + 70 + jobCopy['random_interval'] * 60 + jobCopy['offset'] * 60 #approximate maxRunTime, sanity check
				self.runningJobs[jobId] = jobCopy
				self.calculateNextRunTime(job)
				with self.jobsLock:
					self.jobs.sort(key=lambda job: job['nextRunTime'])

			jobsToRun = [] #jobs to run in a separate list, to avoid deadlocks (necessary?)
			for runningJobId in self.runningJobs.keys():
				runningJob = self.runningJobs[runningJobId]
				if runningJob['nextRunTime'] < time.time():
					if runningJob['maxRunTime'] > time.time():
						isZWaveDevice = True if 'zwave' in runningJob['transport'] else False
						if not isZWaveDevice:
							#repeats for 433-devices only, TODO test
							runningJob['reps'] = int(runningJob['reps']) - 1
							if runningJob['reps'] > 0:
								runningJob['nextRunTime'] = time.time() + 3
								jobsToRun.append(runningJob)
								continue

						if runningJob['retries'] > 0:
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