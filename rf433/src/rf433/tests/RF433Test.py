# -*- coding: utf-8 -*-

import six
import unittest

from ..RF433 import DeviceNode
from ..Protocol import Protocol

class MockController(object):
	def __init__(self):
		self.message = ""

	def queue(self, message):
		self.message = message

class RF433Test(unittest.TestCase):
	def testOutgoingArctech(self):
		mc = MockController()
		device = DeviceNode(mc)
		params = {'type': 'device', 'protocol': 'arctech', 'model': 'selflearning-dimmer:tellduscomen2', 'protocolParams': {'house': '31721280', 'unit': '1'}}
		device.setParams(params)
		device.command(2)  # turn off
		if six.PY2:
			a = [ord(x) for x in mc.message.commandString()]
		else:
			a = list(mc.message.commandBytes())
		b = [83, 24, 255, 24, 24, 24, 127, 24, 127, 24, 24, 24, 127, 24, 24, 24, 127, 24, 24, 24, 127, 24, 24, 24, 24, 24, 127, 24, 24, 24, 127, 24, 127, 24, 24, 24, 24, 24, 127, 24, 24, 24, 127, 24, 24, 24, 127, 24, 24, 24, 127, 24, 24, 24, 127, 24, 24, 24, 127, 24, 24, 24, 127, 24, 127, 24, 24, 24, 127, 24, 24, 24, 127, 24, 24, 24, 24, 24, 127, 24, 127, 24, 24, 24, 24, 24, 127, 24, 24, 24, 127, 24, 24, 24, 127, 24, 24, 24, 127, 24, 24, 24, 127, 24, 24, 24, 127, 24, 24, 24, 127, 24, 24, 24, 127, 24, 24, 24, 127, 24, 24, 24, 127, 24, 24, 24, 127, 24, 24, 24, 127, 24, 43]
		self.assertEqual(a, b, "Incorrect command parsing")

	def testIncomingArctech(self):
		a = Protocol.decodeData({'protocol': 'arctech', 'model': 'selflearning', 'data': '0x3A9DFD9E'})
		c = Protocol.decodeData({'protocol': 'arctech', 'model': 'selflearning', 'data': '0x3A9DFD8D'})
		correctA = [{'protocol': 'arctech', 'house': '15366134', 'method': 1, 'group': 0, 'model': 'selflearning', 'class': 'command', 'unit': '15'}, {'class': 'command', 'protocol': 'arctech', 'house': '15366134', 'model': 'selflearning-bell', 'method': 4, 'unit': '15', 'group': 0}, {'protocol': 'comen', 'house': '3841533', 'method': 1, 'model': 'selflearning', 'class': 'command', 'unit': '15'}]
		correctC = [{'protocol': 'arctech', 'house': '15366134', 'method': 2, 'group': 0, 'model': 'selflearning', 'class': 'command', 'unit': '14'}, {'protocol': 'comen', 'house': '3841533', 'method': 2, 'model': 'selflearning', 'class': 'command', 'unit': '14'}]
		self.assertEqual(a, correctA, "Incorrect incoming Arctech parsing, A")
		self.assertEqual(c, correctC, "Incorrect incoming Arctech parsing, C")
