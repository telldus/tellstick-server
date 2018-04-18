# -*- coding: utf-8 -*-

import base64
import logging
import os
import random
import struct
import time
import uuid

from base import IInterface, ObserverCollection, Plugin, Settings, implements
from web.base import IWebRequestHandler, WebResponseJson
from board import Board

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from jose import jwt, JWSError, JWTError
from pkg_resources import resource_filename

class IApiCallHandler(IInterface):
	"""IInterface for plugin implementing API calls"""

class ApiManager(Plugin):
	implements(IWebRequestHandler)

	observers = ObserverCollection(IApiCallHandler)

	def __init__(self):
		self.tokens = {}
		self.tokenKey = None

	@staticmethod
	def getTemplatesDirs():
		return [resource_filename('api', 'templates')]

	@staticmethod
	def matchRequest(plugin, __path):
		if plugin != 'api':
			return False
		return True

	def handleRequest(self, plugin, path, params, request, **__kwargs):
		del plugin
		if path == '':
			methods = {}
			for observer in self.observers:
				for module, actions in getattr(observer, '_apicalls', {}).iteritems():
					for action, func in actions.iteritems():
						methods.setdefault(module, {})[action] = {'doc': func.__doc__}
			return 'index.html', {'methods': methods}
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
				if self.tokens[token]['allowRenew'] is True:
					body['renew'] = True
					body['ttl'] = self.tokens[token]['ttl']
				accessToken = self.__generateToken(body, claims)
				resp = WebResponseJson({
					'token': accessToken,
					'expires': claims['exp'],
					'allowRenew': self.tokens[token]['allowRenew'],
				})
				del self.tokens[token]
				return resp
		if path == 'authorize':
			if 'token' not in params:
				return WebResponseJson({'error': 'No token specified'}, statusCode=400)
			token = params['token']
			if token not in self.tokens:
				return WebResponseJson({'error': 'No such token'}, statusCode=404)
			if request.method() == 'POST':
				self.tokens[token]['authorized'] = True
				self.tokens[token]['allowRenew'] = bool(request.post('extend', False))
				self.tokens[token]['ttl'] = int(request.post('ttl', 0))*60
			return 'authorize.html', {'token': self.tokens[token]}

		# Check authorization
		token = request.header('Authorization')
		if token is None:
			return WebResponseJson({'error': 'No token was found in the request'}, statusCode=401)
		if not token.startswith('Bearer '):
			return WebResponseJson(
				{
					'error': 'The autorization token must be supplied as a bearer token'
				},
				statusCode=401
			)
		token = token[7:]
		try:
			body = jwt.decode(token, self.__tokenKey(), algorithms='HS256')
		except JWSError as error:
			return WebResponseJson({'error': str(error)}, statusCode=401)
		except JWTError as error:
			return WebResponseJson({'error': str(error)}, statusCode=401)
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
			accessToken = self.__generateToken({
				'renew': True,
				'ttl': ttl
			}, {
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
		module = paths[0]
		action = paths[1]
		for observer in self.observers:
			func = getattr(observer, '_apicalls', {}).get(module, {}).get(action, None)
			if func is None:
				continue
			try:
				params['app'] = aud
				retval = func(observer, **params)
			except Exception as error:
				logging.exception(error)
				return WebResponseJson({'error': str(error)})
			if retval is True:
				retval = {'status': 'success'}
			return WebResponseJson(retval)
		return WebResponseJson(
			{'error': 'The method %s/%s does not exist' % (module, action)},
			statusCode=404
		)

	@staticmethod
	def requireAuthentication(plugin, path):
		if plugin != 'api':
			return
		if path in ['', 'authorize']:
			return True
		return False

	def __tokenKey(self):
		if self.tokenKey is not None:
			return self.tokenKey
		password = Board.secret()
		settings = Settings('telldus.api')
		tokenKey = settings.get('tokenKey', '')
		backend = default_backend()
		blockSize = 16  # TODO: Get this programatically?
		if tokenKey == '':
			self.tokenKey = os.urandom(32)
			# Store it
			salt = os.urandom(16)
			kdf = PBKDF2HMAC(
				algorithm=hashes.SHA1(),
				length=32,
				salt=salt,
				iterations=1000,
				backend=backend
			)
			key = kdf.derive(password)
			pwhash = ApiManager.pbkdf2crypt(password)
			settings['salt'] = base64.b64encode(salt)
			settings['pw'] = pwhash
			# Encrypt token key
			cipher = Cipher(algorithms.AES(key), modes.ECB(), backend=backend)
			encryptor = cipher.encryptor()
			buf = bytearray(len(self.tokenKey)+blockSize-1)
			lenEncrypted = encryptor.update_into(self.tokenKey, buf)
			settings['tokenKey'] = base64.b64encode(bytes(buf[:lenEncrypted]) + encryptor.finalize())
		else:
			# Decode it
			salt = base64.b64decode(settings.get('salt', ''))
			pwhash = settings.get('pw', '')
			if ApiManager.pbkdf2crypt(password, pwhash) != pwhash:
				logging.warning('Could not decrypt token key, wrong password')
				return None
			kdf = PBKDF2HMAC(
				algorithm=hashes.SHA1(),
				length=32,
				salt=salt,
				iterations=1000,
				backend=backend
			)
			key = kdf.derive(password)
			enc = base64.b64decode(tokenKey)
			cipher = Cipher(algorithms.AES(key), modes.ECB(), backend=backend)
			decryptor = cipher.decryptor()
			buf = bytearray(len(enc)+blockSize-1)
			lenDecrypted = decryptor.update_into(enc, buf)
			self.tokenKey = bytes(buf[:lenDecrypted]) + decryptor.finalize()

		return self.tokenKey

	def __generateToken(self, body, claims):
		return jwt.encode(body, self.__tokenKey(), algorithm='HS256', headers=claims)

	@staticmethod
	def apicall(module, action):
		def call(func):
			import sys
			frame = sys._getframe(1)  # pylint: disable=W0212
			frame.f_locals.setdefault('_apicalls', {}).setdefault(module, {})[action] = func
			return func
		return call

	@staticmethod
	def pbkdf2crypt(password, salt=None):
		if salt is None:
			binarysalt = b''.join([struct.pack("@H", random.randint(0, 0xffff)) for _i in range(3)])
			salt = "$p5k2$$" + base64.b64encode(binarysalt, "./")
		elif salt.startswith("$p5k2$"):
			salt = "$p5k2$$" + salt.split("$")[3]
		kdf = PBKDF2HMAC(
			algorithm=hashes.SHA1(),
			length=24,
			salt=salt,
			iterations=400,
			backend=default_backend()
		)
		rawhash = kdf.derive(password)
		return salt + "$" + base64.b64encode(rawhash, "./")

apicall = ApiManager.apicall  # pylint: disable=C0103
