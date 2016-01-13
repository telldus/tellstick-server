# -*- coding: utf-8 -*-

from base import Application, Plugin, Settings, implements, mainthread
from web.base import IWebRequestHandler, WebResponseRedirect, Server
from telldus import DeviceManager, Sensor
from threading import Thread
from pkg_resources import resource_filename
import rauth, json, time

class NetatmoModule(Sensor):
	def __init__(self, _id, name, type):
		super(NetatmoModule,self).__init__()
		self._localId = _id
		self.batteryLevel = None
		self._type = type
		self.setName(name)

	def battery(self):
		if self.batteryLevel is None:
			return None
		# Ugly workaround until battery has been properly fixed...
		class Object(object):
			pass
		battery = Object()
		battery.level = self.batteryLevel
		return battery

	def localId(self):
		return self._localId

	def model(self):
		return self._type

	def typeString(self):
		return 'netatmo'

class Netatmo(Plugin):
	implements(IWebRequestHandler)

	supportedTypes = {
		'Temperature': (Sensor.TEMPERATURE, Sensor.SCALE_TEMPERATURE_CELCIUS),
		'Humidity': (Sensor.HUMIDITY, Sensor.SCALE_HUMIDITY_PERCENT),
		'CO2': (Sensor.UNKNOWN, Sensor.SCALE_UNKNOWN),
		#'Noise':,
		#'Pressure': (Sensor.BAROMETRIC_PRESSURE, Sensor.SCALE_UNKNOWN),
		'Rain': (Sensor.RAINTOTAL, Sensor.SCALE_RAINTOTAL_MM),
		'WindAngle': (Sensor.WINDDIRECTION, Sensor.SCALE_WIND_DIRECTION),
		'WindStrength': (Sensor.WINDAVERAGE, Sensor.SCALE_WIND_VELOCITY_MS),
		'GustStrength': (Sensor.WINDGUST, Sensor.SCALE_WIND_VELOCITY_MS),
	}
	products = {
#		'NAMain': {}  # Base station
		'NAModule1': {'batteryMax': 6000, 'batteryMin': 3600},  # Outdoor module
		'NAModule4': {'batteryMax': 6000, 'batteryMin': 4200},  # Additional indoor module
		'NAModule3': {'batteryMax': 6000, 'batteryMin': 3600},  # Rain gauge
		'NAModule2': {'batteryMax': 6000, 'batteryMin': 3950},  # Wind gauge
#		'NAPlug': {},  # Thermostat relay/plug
#		'NATherm1': {},  # Thermostat module
	}

	def __init__(self):
		self.s = Settings('netatmo')
		self.deviceManager = DeviceManager(self.context)
		self.sensors = {}
		self.loaded = False
		self.clientId = ''
		self.clientSecret = ''
		self.accessToken = self.s.get('accessToken', '')
		self.refreshToken = self.s.get('refreshToken', '')
		self.tokenTTL = self.s.get('tokenTTL', 0)
		Application().registerScheduledTask(minutes=10, runAtOnce=True, fn=self.__requestNewValues)

	def getTemplatesDirs(self):
		return [resource_filename('netatmo', 'templates')]

	def matchRequest(self, plugin, path):
		if plugin != 'netatmo':
			return False
		if path in ['', 'code']:
			return True
		return False

	def handleRequest(self, plugin, path, params, request, **kwargs):
		# Web requests
		if self.accessToken == '':
			service = rauth.OAuth2Service(
				client_id=self.clientId,
				client_secret=self.clientSecret,
				access_token_url='https://api.netatmo.net/oauth2/token',
				authorize_url='https://api.netatmo.net/oauth2/authorize'
			)
			if path == '':
				params = {'redirect_uri': '%s/netatmo/code' % request.base(),
				          'response_type': 'code'}
				url = service.get_authorize_url(**params)
				return WebResponseRedirect(url)
			elif path == 'code':
				data = {'code': params['code'],
				        'grant_type': 'authorization_code',
				        'redirect_uri': '%s/netatmo/code' % request.base()
				}
				session = service.get_auth_session(data=data, decoder=self.__decodeAccessToken)
			return WebResponseRedirect('/')
		return 'netatmo.html', {}

	def __addUpdateDevice(self, data):
		if data['_id'] not in self.sensors:
			sensor = NetatmoModule(data['_id'], data['module_name'], data['type'])
			self.deviceManager.addDevice(sensor)
			self.sensors[data['_id']] = sensor
		else:
			sensor = self.sensors[data['_id']]
		for dataType in Netatmo.supportedTypes:
			if dataType not in data['dashboard_data']:
				continue
			valueType, scale = Netatmo.supportedTypes[dataType]
			value = data['dashboard_data'][dataType]
			if dataType == 'WindStrength' or dataType == 'GustStrength':
				value = round(value / 3.6, 2)  # Data is reported in km/h, we want m/s
			sensor.setSensorValue(valueType, value, scale)
		if 'battery_vp' in data and data['type'] in Netatmo.products:
			product = Netatmo.products[data['type']]
			battery = 1.0*max(min(data['battery_vp'], product['batteryMax']), product['batteryMin'])
			sensor.batteryLevel = int((battery - product['batteryMin'])/(product['batteryMax'] - product['batteryMin'])*100)

	@mainthread
	def __parseValues(self, data):
		if 'body' not in data:
			return
		body = data['body']
		if 'devices' not in body:
			return
		devices = body['devices']
		for device in devices:
			self.__addUpdateDevice(device)
			for module in device['modules']:
				self.__addUpdateDevice(module)
		if self.loaded == False:
			self.loaded = True
			self.deviceManager.finishedLoading('netatmo')

	def __requestNewValues(self):
		if self.accessToken == '':
			return
		def backgroundTask():
			service = rauth.OAuth2Service(
				client_id=self.clientId,
				client_secret=self.clientSecret,
				access_token_url='https://api.netatmo.net/oauth2/token'
			)
			if time.time() > self.tokenTTL:
				session = self.__requestSession(service)
			else:
				session = rauth.OAuth2Session(self.clientId,self.clientSecret,access_token=self.accessToken,service=service)
			response = session.get('https://api.netatmo.com/api/getstationsdata')
			data = response.json()
			if 'error' in data and data['error']['code'] in [2, 3]:
				# Token is expired. Request new
				session = self.__requestSession(service)
				response = session.get('https://api.netatmo.com/api/getstationsdata')
				data = response.json()
			self.__parseValues(data)
		Thread(target=backgroundTask).start()

	def __requestSession(self, service):
		data = {'grant_type': 'refresh_token',
		        'refresh_token': self.refreshToken}
		session = service.get_auth_session(data=data, decoder=self.__decodeAccessToken)
		return session

	def __decodeAccessToken(self, data):
		response = json.loads(data)
		self.accessToken = response['access_token']
		self.refreshToken = response['refresh_token']
		self.tokenTTL = int(time.time()) + response['expires_in']
		self.s['accessToken'] = self.accessToken
		self.s['refreshToken'] = self.refreshToken
		self.s['tokenTTL'] = self.tokenTTL
		return response
