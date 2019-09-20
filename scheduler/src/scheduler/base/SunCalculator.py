# -*- coding: utf-8 -*-

#Based on Stephen R. Schmitts calculator
#http://mysite.verizon.net/res148h4j/javascript/script_sun_rise_set.html

import math
from datetime import datetime
from calendar import timegm

class SunCalculator:

	def __init__(self):
		self.DR = math.pi/180
		self.K1 = 15*self.DR*1.0027379

		self.Sunrise = False
		self.Sunset  = False

		self.Rise_time = [0, 0]
		self.Set_time  = [0, 0]
		self.Rise_az = 0.0
		self.Set_az  = 0.0

		self.Sky = [0.0, 0.0]
		self.RAn = [0.0, 0.0, 0.0]
		self.Dec = [0.0, 0.0, 0.0]
		self.VHz = [0.0, 0.0, 0.0]

	def nextRiseSet(self, date, lat, lon):
		retval = {'sunrise': 0, 'sunset': 0}
		curDate = date
		while retval['sunrise'] == 0 or retval['sunset'] == 0:
			values = self.riseset(date, lat, lon)
			if retval['sunrise'] == 0 and values['sunrise'] > 0:
				if values['sunrise'] >= curDate:
					retval['sunrise'] = values['sunrise']
			if retval['sunset'] == 0 and values['sunset'] > 0:
				if values['sunset'] >= curDate:
					retval['sunset'] = values['sunset']
			date = date + 60*60*24  # One day later
			#break
		return retval

	# calculate sunrise and sunset times
	def riseset(self, date, lat, lon):
		d = datetime.utcfromtimestamp(date)

		jd = self.julian_day(date) - 2451545  # Julian day relative to Jan 1.5, 2000

		lon = lon/360
		ct  = jd/36525 + 1 #  centuries since 1900.0
		t0 = self.lst(lon, jd)  # local sidereal time

		#jd = jd + tz  # get sun position at start of day
		self.sun(jd, ct)
		ra0  = self.Sky[0]
		dec0 = self.Sky[1]

		jd = jd + 1  # get sun position at end of day
		self.sun(jd, ct)
		ra1  = self.Sky[0]
		dec1 = self.Sky[1]

		if ra1 < ra0:  # make continuous
			ra1 = ra1 + 2*math.pi

		self.Sunrise = False  # initialize
		self.Sunset  = False
		self.RAn[0]  = ra0
		self.Dec[0]  = dec0

		for k in range(24):  # check each hour of this day
			ph = (k + 1.0)/24

			self.RAn[2] = ra0  + (k + 1)*(ra1  - ra0)/24
			self.Dec[2] = dec0 + (k + 1)*(dec1 - dec0)/24
			self.VHz[2] = self.test_hour(k, t0, lat, date)

			self.RAn[0] = self.RAn[2]  # advance to next hour
			self.Dec[0] = self.Dec[2]
			self.VHz[0] = self.VHz[2]

		# display results
		values = {'sunrise': None, 'sunset': None}

		if self.Sunrise:
			values['sunrise'] = timegm(datetime(d.year, d.month, d.day, int(self.Rise_time[0]), int(self.Rise_time[1]), 0).utctimetuple())
		if self.Sunset:
			values['sunset'] = timegm(datetime(d.year, d.month, d.day, int(self.Set_time[0]), int(self.Set_time[1]), 0).utctimetuple())
		return values

	# Local Sidereal Time for zone
	def lst(self, lon, jd):
		s = 24110.5 + 8640184.812999999*jd/36525 + 86400*lon
		s = s/86400
		s = s - math.floor(s)
		return s*360*self.DR

	# test an hour for an event
	def test_hour(self, k, t0, lat, date):
		ha = [0, 0, 0]

		ha[0] = t0 - self.RAn[0] + k*self.K1
		ha[2] = t0 - self.RAn[2] + k*self.K1 + self.K1

		ha[1]  = (ha[2]  + ha[0])/2  # hour angle at half hour
		self.Dec[1] = (self.Dec[2] + self.Dec[0])/2  # declination at half hour

		s = math.sin(lat*self.DR)
		c = math.cos(lat*self.DR)

		zenith = 90.833  # default
		z = math.cos(zenith*self.DR)  # refraction + sun semidiameter at horizon

		if k <= 0:
			self.VHz[0] = s*math.sin(self.Dec[0]) + c*math.cos(self.Dec[0])*math.cos(ha[0]) - z

		self.VHz[2] = s*math.sin(self.Dec[2]) + c*math.cos(self.Dec[2])*math.cos(ha[2]) - z

		if self.sgn(self.VHz[0]) == self.sgn(self.VHz[2]):
			return self.VHz[2]  # no event this hour

		self.VHz[1] = s*math.sin(self.Dec[1]) + c*math.cos(self.Dec[1])*math.cos(ha[1]) - z

		a =  2* self.VHz[0] - 4*self.VHz[1] + 2*self.VHz[2]
		b = -3* self.VHz[0] + 4*self.VHz[1] - self.VHz[2]
		d = b*b - 4*a*self.VHz[0]

		if d < 0:
			return self.VHz[2]  # no event this hour

		d = math.sqrt(d)
		e = (-b + d)/(2 * a)

		if e > 1 or e < 0:
			e = (-b - d)/(2*a)

		time = k + e + 1.0/120.0  # time of an event

		hr = math.floor(time)
		min = math.floor((time - hr)*60)

		hz = ha[0] + e*(ha[2] - ha[0])  # azimuth of the sun at the event
		nz = -math.cos(self.Dec[1])*math.sin(hz)
		dz = c*math.sin(self.Dec[1]) - s*math.cos(self.Dec[1])*math.cos(hz)
		az = math.atan2(nz, dz)/self.DR
		if az < 0:
			az = az + 360

		if self.VHz[0] < 0 and self.VHz[2] > 0:
			self.Rise_time[0] = hr
			self.Rise_time[1] = min
			self.Rise_az = az
			self.Sunrise = True

		if self.VHz[0] > 0 and self.VHz[2] < 0:
			self.Set_time[0] = hr
			self.Set_time[1] = min
			self.Set_az = az
			self.Sunset = True

		return self.VHz[2]

	# sun's position using fundamental arguments
	# (Van Flandern & Pulkkinen, 1979)
	def sun(self, jd, ct ):
		lo = 0.779072 + 0.00273790931*jd
		lo = lo - math.floor(lo)
		lo = lo*2*math.pi

		g = 0.993126 + 0.0027377785*jd
		g = g - math.floor(g)
		g = g*2*math.pi

		v = 0.39785*math.sin(lo)
		v = v - 0.01*math.sin(lo - g)
		v = v + 0.00333*math.sin(lo + g)
		v = v - 0.00021*ct * math.sin(lo)

		u = 1 - 0.03349*math.cos(g)
		u = u - 0.00014*math.cos(2*lo)
		u = u + 0.00008*math.cos(lo)

		w = -0.0001 - 0.04129*math.sin(2*lo)
		w = w + 0.03211*math.sin(g)
		w = w + 0.00104*math.sin(2*lo - g)
		w = w - 0.00035*math.sin(2*lo + g)
		w = w - 0.00008*ct*math.sin(g)
		s = w/math.sqrt(u - v*v)  # compute sun's right ascension
		self.Sky[0] = lo + math.atan(s/math.sqrt(1 - s*s))

		s = v/math.sqrt(u)  # ...and declination
		self.Sky[1] = math.atan(s/math.sqrt(1 - s*s))

	# determine Julian day from calendar date
	# (Jean Meeus, "Astronomical Algorithms", Willmann-Bell, 1991)
	def julian_day(self, date):
		d = datetime.utcfromtimestamp(date)
		month = d.month
		day   = d.day
		year  = d.year

		if month == 1 or month == 2:
			year  = year  - 1
			month = month + 12

		a = math.floor(year/100)
		b = 2 - a + math.floor(a/4)

		jd = math.floor(365.25*(year + 4716)) + math.floor(30.6001*(month + 1)) + day + b - 1524.5

		return jd

	# returns value for sign of argument
	def sgn(self, x):
		if x > 0.0:
			rv =  1
		elif x < 0.0:
			rv = -1
		else:
			rv = 0
		return rv

if __name__ == '__main__':
	def test(date, lat, lon, sunrise, sunset):
		s = SunCalculator()
		r = s.nextRiseSet(date, lat, lon)
		ok = 'OK' if r['sunrise'] == sunrise and r['sunset'] == sunset else 'NOT OK'
		print(f"{ok} - {str(r['sunrise'])}=={str(sunrise)}, {str(r['sunset'])}=={str(sunset)}")
	test(1396316636, 55.69, 13.18, 1396327140, 1396374300)
	test(1410755983, 55.69, 13.18, 1410842460, 1410801900)
	test(1403490211, 55.69, 13.18, 1403576640, 1403553360)
	test(1395550851, 55.69, 13.18, 1395550920, 1395595620)
	test(1419233723, 55.69, 13.18, 1419320160, 1419258960)
	test(1408673976, 69.05, 20.5, 1408760460, 1408734120)
	test(1416646171, 69.05, 20.5, 1416732900, 1416657540)
	test(1417341653, 69.05, 20.5, 1421057940, 1421061240)
	test(1396237617, 69.05, 20.5, 1396237800, 1396287420)
	test(1419731036, 69.05, 20.5, 1421057940, 1421061240)
