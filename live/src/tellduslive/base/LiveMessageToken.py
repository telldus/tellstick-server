# -*- coding: utf-8 -*-

import base64
import uuid

class LiveMessageToken(object):
	TYPE_INVALID, TYPE_INT, TYPE_STRING, TYPE_BASE64, TYPE_LIST, TYPE_DICTIONARY = list(range(6))

	def __init__(self, value=None):
		self.valueType = LiveMessageToken.TYPE_INVALID
		self.byteVal = b''
		self.intVal = 0
		self.dictVal = {}
		self.listVal = []
		if isinstance(value, int):
			self.valueType = self.TYPE_INT
			self.intVal = value
		elif isinstance(value, bool):
			self.valueType = self.TYPE_INT
			self.intVal = int(value)
		elif isinstance(value, str):
			self.valueType = self.TYPE_STRING
			self.byteVal = value.encode()
		elif isinstance(value, list):
			self.valueType = self.TYPE_LIST
			for item in value:
				self.listVal.append(LiveMessageToken(item))
		elif isinstance(value, dict):
			self.valueType = self.TYPE_DICTIONARY
			for key in value:
				self.dictVal[key] = LiveMessageToken(value[key])
		elif isinstance(value, float):
			self.valueType = self.TYPE_STRING
			self.byteVal = str(value).encode()
		elif isinstance(value, uuid.UUID):
			self.valueType = self.TYPE_STRING
			self.byteVal = str(value).encode()
		elif isinstance(value, bytearray):
			self.valueType = self.TYPE_STRING
			self.byteVal = value

	def toJSON(self):
		if self.valueType == LiveMessageToken.TYPE_INT:
			return '%d' % self.intVal

		if self.valueType == LiveMessageToken.TYPE_LIST:
			retval = '['
			for token in self.listVal:
				if len(retval) > 1:
					retval = retval + ","
				retval = retval + token.toJSON()
			return retval + ']'

		if self.valueType == LiveMessageToken.TYPE_DICTIONARY:
			retval = '{'
			for key in self.dictVal:
				if len(retval) > 1:
					retval = retval + ","
				retval = retval + LiveMessageToken(key).toJSON() + "=" + self.dictVal[key].toJSON()
			return retval + '}'

		return self.stringVal

	def toNative(self):
		if self.valueType == LiveMessageToken.TYPE_INT:
			return self.intVal

		if self.valueType == LiveMessageToken.TYPE_LIST:
			retval = []
			for token in self.listVal:
				retval.append(token.toNative())
			return retval

		if self.valueType == LiveMessageToken.TYPE_DICTIONARY:
			retdict = {}
			for key in self.dictVal:
				retdict[key] = self.dictVal[key].toNative()
			return retdict

		return self.stringVal

	def toByteArray(self, base64encode=True):
		if self.valueType == LiveMessageToken.TYPE_INT:
			return b'i%Xs' % self.intVal

		if self.valueType == LiveMessageToken.TYPE_LIST:
			retval = b'l'
			for token in self.listVal:
				retval = retval + token.toByteArray(base64encode)
			return retval + b's'

		if self.valueType == LiveMessageToken.TYPE_DICTIONARY:
			retval = b'h'
			for key in self.dictVal:
				retval = retval + LiveMessageToken(str(key)).toByteArray(base64encode) + self.dictVal[key].toByteArray(base64encode)
			return retval + b's'

		if base64encode:
			stringVal = base64.b64encode(self.byteVal)
			return b'u%X:%s' % (len(stringVal), stringVal,)
		return b'%X:%s' % (len(self.byteVal), self.byteVal,)

	@staticmethod
	def parseToken(bArray, start):
		token = LiveMessageToken()
		if start >= len(bArray):
			return (start, token)

		if bArray[start] == ord('i'):
			start += 1
			index = bArray.find(ord('s'), start)
			if index < 0:
				return (start, token)

			try:
				token.intVal = int(bArray[start:index], 16)
				token.valueType = LiveMessageToken.TYPE_INT
				start = index + 1
			except Exception:
				return (start, token)

		elif bArray[start] == ord('l'):
			start += 1
			token.valueType = LiveMessageToken.TYPE_LIST
			while start < len(bArray) and bArray[start] != ord('s'):
				start, listToken = LiveMessageToken.parseToken(bArray, start)
				if listToken.valueType == LiveMessageToken.TYPE_INVALID:
					break
				token.listVal.append(listToken)
			start += 1

		elif bArray[start] == ord('h'):
			start += 1
			token.valueType = LiveMessageToken.TYPE_DICTIONARY
			while start < len(bArray) and bArray[start] != ord('s'):
				start, keyToken = LiveMessageToken.parseToken(bArray, start)
				if keyToken.valueType == LiveMessageToken.TYPE_STRING:
					key = keyToken.stringVal
				elif keyToken.valueType == LiveMessageToken.TYPE_INT:
					key = keyToken.intVal
				else:
					break
				start, valueToken = LiveMessageToken.parseToken(bArray, start)
				if valueToken.valueType == LiveMessageToken.TYPE_INVALID:
					break
				token.dictVal[key] = valueToken
			start += 1
		elif bArray[start] == ord('u'):  # Base64
			# TODO, needs testing
			start += 1
			start, token = LiveMessageToken.parseToken(bArray, start)
			token.valueType = LiveMessageToken.TYPE_BASE64
			token.byteVal = base64.encodestring(token.byteVal)

		else: #String
			index = bArray.find(ord(':'), start)
			if index < 0:
				return (start, token)

			try:
				length = int(bArray[start:index], 16)
			except Exception:
				return (start, token)

			start = index + length + 1
			token.byteVal = bArray[index+1:start]
			token.valueType = LiveMessageToken.TYPE_STRING

		return (start, token)

	@property
	def stringVal(self):
		return self.byteVal.decode()