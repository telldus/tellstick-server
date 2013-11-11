# -*- coding: utf-8 -*-

import base64
import logging

class LiveMessageToken(object):
	TYPE_INVALID, TYPE_INT, TYPE_STRING, TYPE_BASE64, TYPE_LIST, TYPE_DICTIONARY = range(6)

	def __init__(self, value = None):
		self.valueType = LiveMessageToken.TYPE_INVALID
		self.stringVal = u''
		self.intVal = 0
		self.dictVal = {}
		self.listVal = []
		if (type(value) is int):
			self.valueType = self.TYPE_INT
			self.intVal = value

		elif (type(value) is str or type(value) is unicode):
			self.valueType = self.TYPE_STRING
			self.stringVal = value

		elif (type(value) is list):
			self.valueType = self.TYPE_LIST
			for v in value:
				self.listVal.append(LiveMessageToken(v))

		elif (type(value) is dict):
			self.valueType = self.TYPE_DICTIONARY
			for key in value:
				self.dictVal[key] = LiveMessageToken(value[key])

	def toJSON(self):
		if (self.valueType == LiveMessageToken.TYPE_INT):
			return '%d' % self.intVal

		if (self.valueType == LiveMessageToken.TYPE_LIST):
			retval = '['
			for token in self.listVal:
				if len(retval) > 1:
					retval = retval + ","
				retval = retval + token.toJSON()
			return retval + ']'

		if (self.valueType == LiveMessageToken.TYPE_DICTIONARY):
			retval = '{'
			for key in self.dictVal:
				if len(retval) > 1:
					retval = retval + ","
				retval = retval + LiveMessageToken(key).toJSON() + "=" + self.dictVal[key].toJSON()
			return retval + '}'

		return self.stringVal

	def toByteArray(self):
		if (self.valueType == LiveMessageToken.TYPE_INT):
			return 'i%Xs' % self.intVal

		if (self.valueType == LiveMessageToken.TYPE_LIST):
			retval = 'l'
			for token in self.listVal:
				retval = retval + token.toByteArray()
			return retval + 's'

		if (self.valueType == LiveMessageToken.TYPE_DICTIONARY):
			retval = 'h'
			for key in self.dictVal:
				retval = retval + LiveMessageToken(key).toByteArray() + self.dictVal[key].toByteArray()
			return retval + 's'

		if type(self.stringVal) == unicode:
			s = base64.encodestring(self.stringVal.encode('utf-8'))
			return 'u%X:%s' % (len(s), str(s),)

		return '%X:%s' % (len(self.stringVal), str(self.stringVal),)

	@staticmethod
	def parseToken(string, start):
		token = LiveMessageToken()
		if (start >= len(string)):
			return (start, token)

		if (string[start] == 'i'):
			start+=1
			index = string.find('s', start)
			if (index < 0):
				return (start, token)

			try:
				token.intVal = int(string[start:index], 16)
				token.valueType = LiveMessageToken.TYPE_INT
				start = index + 1
			except:
				return (start, token)

		elif (string[start] == 'l'):
			start+=1
			while (start < len(string) and string[start] != 's'):
				start, listToken = LiveMessageToken.parseToken(string, start)
				if (listToken.valueType == LiveMessageToken.TYPE_INVALID):
					break
				token.valueType = LiveMessageToken.TYPE_LIST
				token.listVal.append(listToken)
			start+=1

		elif (string[start] == 'h'):
			start+=1
			while (start < len(string) and string[start] != 's'):
				start, keyToken = LiveMessageToken.parseToken(string, start)
				if (keyToken.valueType == LiveMessageToken.TYPE_INVALID):
					break
				start, valueToken = LiveMessageToken.parseToken(string, start)
				if (valueToken.valueType == LiveMessageToken.TYPE_INVALID):
					break
				token.valueType = LiveMessageToken.TYPE_DICTIONARY
				token.dictVal[keyToken.stringVal] = valueToken
			start+=1

		elif (string[start] == 'u'): #Base64
			start+=1
			start, token = LiveMessageToken.parseToken(string, start)
			token.valueType = LiveMessageToken.TYPE_BASE64
			token.stringVal = unicode(base64.decodestring(token.stringVal), 'utf-8')

		else: #String
			index = string.find(':', start)
			if (index < 0):
				return (start, token)

			try:
				length = int(string[start:index], 16)
			except:
				return (start, token)

			start = index + length + 1
			token.stringVal = string[index+1:start]
			token.valueType = LiveMessageToken.TYPE_STRING

		return (start, token)

