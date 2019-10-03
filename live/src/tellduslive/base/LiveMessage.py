# -*- coding: utf-8 -*-

import hashlib
from .LiveMessageToken import LiveMessageToken

class LiveMessage():
	def __init__(self, name=""):
		if (name != ""):
			self.args = [LiveMessageToken(name)]
		else:
			self.args = []

	def append(self, argument):
		self.args.append(LiveMessageToken(argument))

	def argument(self, index):
		if (len(self.args) > index+1):
			return self.args[index+1]

		return LiveMessageToken()

	def count(self):
		return len(self.args)-1

	def name(self):
		return self.argument(-1).stringVal.lower()

	def toByteArray(self, base64encode=True):
		retval = bytearray()
		for arg in self.args:
			retval.extend(arg.toByteArray(base64encode))
		return retval

	def toSignedMessage(self, hashMethod, privateKey):
		message = self.toByteArray()
		envelope = LiveMessage(LiveMessage.signatureForMessage(message, hashMethod, privateKey))
		envelope.append(message)
		return envelope.toByteArray(False)  # don't want to base64-encode the already base64-encoded data again

	def verifySignature(self, hashMethod, privateKey):
		signature = self.name()
		rawMessage = self.argument(0).stringVal
		return (self.signatureForMessage(rawMessage, hashMethod, privateKey) == signature)

	@staticmethod
	def fromByteArray(bArray):
		list = []
		start = 0
		while (start < len(bArray)):
			start, token = LiveMessageToken.parseToken(bArray, start)
			if (token.valueType == LiveMessageToken.TYPE_INVALID):
				break
			list.append(token)

		msg = LiveMessage()
		msg.args = list
		return msg

	@staticmethod
	def signatureForMessage(msg, hashMethod, privateKey):
		h = 0
		if (hashMethod == "sha512"):
			h = hashlib.sha512()
		elif (hashMethod == "sha256"):
			h = hashlib.sha256()
		else:
			h = hashlib.sha1()

		if isinstance(msg, str):
			h.update(msg.encode())
		else:
			h.update(msg)
		h.update(privateKey.encode())
		return h.hexdigest().lower()
