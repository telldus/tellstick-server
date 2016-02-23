# -*- coding: utf-8 -*-

from base import implements, Plugin, Settings
from web.base import IWebRequestHandler, WebResponseRedirect
from pkg_resources import resource_filename
from upnp import SSDP, ISSDPNotifier
from telldus import DeviceManager, Device, DeviceAbortException
import colorsys, logging
import httplib, urlparse, json

class Bridge(object):
	def __init__(self, config):
		pass

class Light(Device):
	def __init__(self, nodeId, bridge):
		super(Light,self).__init__()
		self._nodeId = nodeId
		self._bridge = bridge
		self._type = 'unknown'

	def _command(self, action, value, success, failure, **kwargs):
		if action == Device.TURNON:
			msg = '{"on": true, "bri": 254}'
		elif action == Device.TURNOFF:
			msg = '{"on": false}'
		elif action == Device.DIM:
			msg = '{"on": true, "bri": %s}' % value
		elif action == Device.RGBW:
			value = int(value, 16)
			r = (value >> 24) & 0xFF
			g = (value >> 16) & 0xFF
			b = (value >> 8) & 0xFF
			h, s, v = colorsys.rgb_to_hsv(r, g, b)
			msg = '{"on": true, "hue": %i, "sat": %i}' % (h*65535, s*254)
		else:
			failure(0)
			return
		retval = self._bridge.doCall('PUT', '/api/%s/lights/%s/state' % (self._bridge.username, self._nodeId), msg)
		if len(retval) == 0 or 'success' not in retval[0]:
			failure(0)
			return
		state = 0
		value = None
		for v in retval:
			if 'success' not in v:
				continue
			s = v['success']
			if '/lights/%s/state/on' % self._nodeId in s:
				on = s['/lights/%s/state/on' % self._nodeId]
				if on == False:
					state = Device.TURNOFF
					break
			elif '/lights/%s/state/bri' % self._nodeId in s:
				bri = s['/lights/%s/state/bri' % self._nodeId]
				if bri == 254:
					state = Device.TURNON
					break
				else:
					state = Device.DIM
					value = bri
		if state == 0:
			failure(0)
		success()

	def localId(self):
		return self._nodeId

	def typeString(self):
		return 'hue'

	def isDevice(self):
		return True

	def isSensor(self):
		return False

	def methods(self):
		if self._type in ['Extended color light', 'Color light']:
			return Device.TURNON | Device.TURNOFF | Device.DIM | Device.RGBW
		if self._type in ['Dimmable light', 'Color temperature light']:
			return Device.TURNON | Device.TURNOFF | Device.DIM
		# Unknown type
		return Device.TURNON | Device.TURNOFF | Device.DIM

	def setType(self, type):
		self._type = type

class Hue(Plugin):
	implements(IWebRequestHandler)
	implements(ISSDPNotifier)
	STATE_NO_BRIDGE, STATE_UNAUTHORIZED, STATE_AUTHORIZED = range(3)

	def __init__(self):
		self.deviceManager = DeviceManager(self.context)
		self.s = Settings('philips.hue')
		self.username = None
		self.ssdp = None
		self.activated = self.s.get('activated', False)
		self.state = Hue.STATE_NO_BRIDGE
		if not self.activated:
			return
		self.selectBridge(self.s['bridge'])

	def authorize(self):
		username = self.s['username']
		if username is None:
			self.state = Hue.STATE_UNAUTHORIZED
			data = self.doCall('POST', '/api', '{"devicetype": "Telldus#TellStick ZNet"}')
			resp = data[0]
			if 'error' in resp and resp['error']['type'] == 101:
				# Unauthorized, the user needs to press the button
				return
			if 'success' in resp:
				self.username = resp['success']['username']
				self.s['username'] = resp['success']['username']
				self.activated = True
				self.s['activated'] = True
				self.state = Hue.STATE_AUTHORIZED
			else:
				return
		else:
			self.username = username
		# Check if username is ok
		data = self.doCall('GET', '/api/%s/lights' % self.username)
		if 0 in data and 'error' in data[0]:
			self.state = Hue.STATE_UNAUTHORIZED
			self.username = None
			return
		self.state = Hue.STATE_AUTHORIZED
		self.parseInitData(data)

	def doCall(self, type, endpoint, body = ''):
		conn = httplib.HTTPConnection(self.bridge)
		conn.request(type, endpoint, body)
		response = conn.getresponse()
		try:
			rawData = response.read()
			data = json.loads(rawData)
		except:
			logging.warning("Could not parse JSON")
			logging.warning("%s", rawData)
			return {0: {'error': 'Could not parse JSON'}}
		return data

	def getTemplatesDirs(self):
		return [resource_filename('hue', 'templates')]

	def matchRequest(self, plugin, path):
		if plugin != 'hue':
			return False
		if path == '':
			return True
		return False

	def handleRequest(self, plugin, path, params, **kwargs):
		if plugin != 'hue' or path != '':
			return None
		if 'select' in params:
			self.selectBridge(params['select'])
			return WebResponseRedirect('/')
		elif 'reset' in params:
			self.state = Hue.STATE_NO_BRIDGE
			self.s['bridge'] = ''
			self.bridge = None
			return WebResponseRedirect('/')
		if not self.activated and self.ssdp is None:
			self.ssdp = SSDP(self.context)

		if self.state == Hue.STATE_UNAUTHORIZED:
			self.authorize()
		params = {'state':self.state}
		return 'hue.html', params

	def parseInitData(self, data):
		lights = data
		for i in lights:
			light = Light(i, self)
			if 'name' in lights[i]:
				light.setName(lights[i]['name'])
			if 'state' in lights[i]:
				state = lights[i]['state']
				if state['on'] == False:
					light.setState(Device.TURNOFF)
				elif state['bri'] == 254:
					light.setState(Device.TURNON)
				else:
					light.setState(Device.DIM, state['bri'])
			if 'type' in lights[i]:
				light.setType(lights[i]['type'])
			self.deviceManager.addDevice(light)
		self.deviceManager.finishedLoading('hue')

	def ssdpDeviceFound(self, device):
		if self.state != Hue.STATE_NO_BRIDGE:
			return
		if device.type == 'basic:1':
			url = urlparse.urlparse(device.location)
			self.selectBridge(url.netloc)

	def selectBridge(self, urlbase):
		if urlbase == '' or urlbase is None:
			self.state = Hue.STATE_NO_BRIDGE
			self.bridge = None
			return
		self.s['bridge'] = urlbase
		self.bridge = urlbase
		self.authorize()
