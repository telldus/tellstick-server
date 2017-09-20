# -*- coding: utf-8 -*-

from telldus.web import ConfigurationReactComponent
import copy
import json
import rauth

class ConfigurationOAuth2(ConfigurationReactComponent):
	def __init__(self,
		clientId,
		clientSecret,
		accessTokenUrl,
		authorizeUrl,
		baseUrl=None,
		params=None,
		**kwargs
	):
		super(ConfigurationOAuth2, self).__init__('plugins/oauth2', defaultValue={}, **kwargs)
		self.clientId = clientId
		self.clientSecret = clientSecret
		self.accessTokenUrl = accessTokenUrl
		self.activated = False
		self.authorizeUrl = authorizeUrl
		self.baseUrl = baseUrl
		self.params = params or {}
		self.tokenInfo = {}

	def activate(self, redirectUri):
		service = self.__service()
		params = copy.copy(self.params)
		params.setdefault('response_type', 'code')
		params.setdefault('redirect_uri', redirectUri)
		url = service.get_authorize_url(**params)
		return url

	def activateCode(self, code):
		service = self.__service()
		data = {
			'code': code,
			'grant_type': 'authorization_code',
		}
		service.get_auth_session(data=data, decoder=self.__decodeAccessToken)
		return self.tokenInfo

	def serialize(self):
		retval = super(ConfigurationOAuth2, self).serialize()
		retval['activated'] = self.activated
		return retval

	def session(self, accessToken):
		return rauth.OAuth2Session(
			self.clientId,
			self.clientSecret,
			access_token=accessToken,
			service=self.__service()
		)

	def __decodeAccessToken(self, data):
		response = json.loads(data)
		self.tokenInfo = response
		self.activated = True
		return response

	def __service(self):
		return rauth.OAuth2Service(
			client_id=self.clientId,
			client_secret=self.clientSecret,
			access_token_url=self.accessTokenUrl,
			authorize_url=self.authorizeUrl,
			base_url=self.baseUrl
		)
