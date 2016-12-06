# -*- coding: utf-8 -*-

from base import IInterface, ObserverCollection, Plugin, Settings, implements
from web.base import IWebRequestHandler, WebResponseJson
from telldus import IWebReactHandler
from board import Board
from jose import jwt, JWSError
from pbkdf2 import PBKDF2, crypt
from Crypto.Cipher import AES
import base64, json, os, time, uuid
import logging

class IApiCallHandler(IInterface):
	"""IInterface for plugin implementing API calls"""

class ApiManager(Plugin):
	implements(IWebRequestHandler)
	implements(IWebReactHandler)

	observers = ObserverCollection(IApiCallHandler)

	def __init__(self):
		self.tokens = {}
		self.tokenKey = None

	def doCall(self, module, action, app, params):
		for o in self.observers:
			fn = getattr(o, '_apicalls', {}).get(module, {}).get(action, None)
			if fn is None:
				continue
			try:
				params['app'] = app
				retval = fn(o, **params)
			except Exception as e:
				logging.exception(e)
				raise e
			if retval == True:
				retval = {'status': 'success'}
			return retval
		raise Exception('The method %s/%s does not exist' % (module, action))

	def getReactRoutes(self):
		return [{
			'name': 'api',
			'script': 'api/api.js'
		}, {
			'name': 'api/authorize',
			'script': 'api/authorize.js'
		}]

	def matchRequest(self, plugin, path):
		if plugin != 'api':
			return False
		if path == '':
			return False  # Handled by react
		return True

	def handleRequest(self, plugin, path, params, request, **kwargs):
		if path == 'explore':
			if 'params' in params and type(params['params']) is unicode:
				params['params'] = json.loads(params['params'])
			try:
				return WebResponseJson(self.doCall(params['module'], params['action'], 'Explorer', params['params']))
			except Exception as e:
				return WebResponseJson({'error': str(e)}, statusCode=500)

		if path == 'methods':
			methods = {}
			for o in self.observers:
				for module, actions in getattr(o, '_apicalls', {}).iteritems():
					for action, fn in actions.iteritems():
						methods.setdefault(module, {})[action] = {
							'doc': fn.__doc__.strip(),
							'args': list(fn.func_code.co_varnames)[1:fn.func_code.co_argcount],
						}
			return WebResponseJson(methods)

		if path == 'token':
			if request.method() == 'PUT':
				token = uuid.uuid4().hex
				self.tokens[token] = {
					'app': request.post('app'),
					'authorized': False,
				}
				return WebResponseJson({
					'authUrl': '%s/api/authorize?token=%s' % (request.base(), token),
					'token': token
				})
			elif request.method() == 'GET':
				token = params.get('token', None)
				if token is None:
					return WebResponseJson({'error': 'No token specified'}, statusCode=400)
				if token not in self.tokens:
					return WebResponseJson({'error': 'No such token'}, statusCode=404)
				if self.tokens[token]['authorized'] is not True:
					return WebResponseJson({'error': 'Token is not authorized'}, statusCode=403)
				claims = {
					'aud': self.tokens[token]['app'],
					'exp': int(time.time()+self.tokens[token]['ttl']),
				}
				body = {}
				if self.tokens[token]['allowRenew'] == True:
					body['renew'] = True
					body['ttl'] = self.tokens[token]['ttl']
				accessToken = jwt.encode(body, self.__tokenKey(), algorithm='HS256', headers=claims)
				resp = WebResponseJson({
					'token': accessToken,
					'expires': claims['exp'],
					'allowRenew': self.tokens[token]['allowRenew'],
				})
				del self.tokens[token]
				return resp

		if path in ['tokenInfo', 'authorizeToken']:
			token = None
			if request.method() == 'POST':
				token = request.post('token', None)
			elif 'token' in params:
				token = params['token']
			if token is None:
				return WebResponseJson({'error': 'No token specified'}, statusCode=400)
			if token not in self.tokens:
				return WebResponseJson({'error': 'No such token'}, statusCode=404)
			if path == 'authorizeToken' and request.method() == 'POST':
				self.tokens[token]['authorized'] = True
				self.tokens[token]['allowRenew'] = bool(int(request.post('extend', 0)))
				self.tokens[token]['ttl'] = int(request.post('ttl', 0))*60
				self.tokens[token]['extned'] = request.post('extend')
			return WebResponseJson(self.tokens[token])

		# Check authorization
		token = request.header('Authorization')
		if token is None:
			return WebResponseJson({'error': 'No token was found in the request'}, statusCode=401)
		if not token.startswith('Bearer '):
			return WebResponseJson({'error': 'The autorization token must be supplied as a bearer token'}, statusCode=401)
		token = token[7:]
		try:
			body = jwt.decode(token, self.__tokenKey(), algorithms='HS256')
		except JWSError as e:
			return WebResponseJson({'error': str(e)}, statusCode=401)
		claims = jwt.get_unverified_headers(token)
		if 'exp' not in claims or claims['exp'] < time.time():
			return WebResponseJson({'error': 'The token has expired'}, statusCode=401)
		if 'aud' not in claims or claims['aud'] is None:
			return WebResponseJson({'error': 'No app was configured in the token'}, statusCode=401)
		aud = claims['aud']

		if path == 'refreshToken':
			if 'renew' not in body or body['renew'] != True:
				return WebResponseJson({'error': 'The token is not authorized for refresh'}, statusCode=403)
			if 'ttl' not in body:
				return WebResponseJson({'error': 'No TTL was specified in the token'}, statusCode=401)
			ttl = body['ttl']
			exp = int(time.time()+ttl)
			accessToken = jwt.encode({
				'renew': True,
				'ttl': ttl
			}, self.__tokenKey(), algorithm='HS256', headers={
				'aud': aud,
				'exp': exp,
			})
			return WebResponseJson({
				'token': accessToken,
				'expires': exp,
			})
		paths = path.split('/')
		if len(paths) < 2:
			return None
		try:
			return WebResponseJson(self.doCall(paths[0], paths[1], aud, params))
		except Exception as e:
			return WebResponseJson({'error': str(e)}, statusCode=404)

	def requireAuthentication(self, plugin, path):
		if plugin != 'api':
			return
		if path in ['authorizeToken', 'explore', 'methods', 'tokenInfo']:
			return True
		return False

	def __tokenKey(self):
		if self.tokenKey is not None:
			return self.tokenKey
		password = Board.secret()
		s = Settings('telldus.api')
		tokenKey = s.get('tokenKey', '')
		if tokenKey == '':
			self.tokenKey = os.urandom(32)
			# Store it
			salt = os.urandom(16)
			key = PBKDF2(password, salt).read(32)
			pwhash = crypt(password)
			s['salt'] = base64.b64encode(salt)
			s['pw'] = pwhash
			# Encrypt token key
			cipher = AES.new(key, AES.MODE_ECB, '')
			s['tokenKey'] = base64.b64encode(cipher.encrypt(self.tokenKey))
		else:
			# Decode it
			salt = base64.b64decode(s.get('salt', ''))
			pwhash = s.get('pw', '')
			if crypt(password, pwhash) != pwhash:
				logging.warning('Could not decrypt token key, wrong password')
				return None
			key = PBKDF2(password, salt).read(32)
			enc = base64.b64decode(tokenKey)
			cipher = AES.new(key, AES.MODE_ECB, '')
			self.tokenKey = cipher.decrypt(enc)
		return self.tokenKey

	@staticmethod
	def apicall(module, action):
		def call(fn):
			import sys
			frame = sys._getframe(1)
			frame.f_locals.setdefault('_apicalls', {}).setdefault(module, {})[action] = fn
			return fn
		return call

apicall = ApiManager.apicall
