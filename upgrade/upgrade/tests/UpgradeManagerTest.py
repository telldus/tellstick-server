# -*- coding: utf-8 -*-

import os
import unittest

from mock import patch

from ..UpgradeManager import HotFixManager, UpgradeManagerBase

@staticmethod
def fetchVersion(__imageType):
	return '1.2.3'

def loadAppliedHotfixes(self):
	self.appliedHotfixes = []

def writeAppliedHotfixes(__self):
	pass

class HotFixManagerTest(unittest.TestCase):
	@patch.object(UpgradeManagerBase, 'fetchVersion', fetchVersion)
	@patch.object(HotFixManager, 'loadAppliedHotfixes', loadAppliedHotfixes)
	@patch.object(HotFixManager, 'writeAppliedHotfixes', writeAppliedHotfixes)
	def setUp(self):
		HotFixManager.URL = 'https://fw.telldus.com/hotfixes/tests/testcases.yml'
		self.hotfixManager = HotFixManager()
		self.hotfixes = self.hotfixManager.list()

	def testApplied(self):
		self.assertFalse(self.__getHotFix('default')['applied'])
		self.hotfixManager.appliedHotfixes = ['default']
		self.hotfixManager.clearCache()
		self.hotfixes = self.hotfixManager.list()
		self.assertTrue(self.__getHotFix('default')['applied'])

	def testApply(self):
		keyring = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'telldus.gpg'))
		UpgradeManagerBase.KEYRING = keyring
		self.assertFalse(self.hotfixManager.apply('unknown'))

		self.assertFalse(os.path.exists('/tmp/tests/helloworld'))
		self.assertTrue(self.hotfixManager.apply('helloworld'))
		self.assertTrue(os.path.exists('/tmp/tests/helloworld'))
		with open('/tmp/tests/helloworld', 'r') as fd:
			self.assertEqual(fd.read(), 'Hello World!\n')
		os.remove('/tmp/tests/helloworld')

	def testDeployment(self):
		self.assertEqual(self.__getHotFix('default')['deployment'], 'auto')
		self.assertEqual(self.__getHotFix('deployAuto')['deployment'], 'auto')
		self.assertEqual(self.__getHotFix('deployManual')['deployment'], 'manual')
		self.assertEqual(self.__getHotFix('deployMalformed')['deployment'], 'manual')

	def testFiles(self):
		self.assertEqual(self.__getHotFix('invalidSourceFile')['files'], [])

	def testProducts(self):
		self.assertIn('default', self.hotfixes.keys())
		self.assertNotIn('noProduct', self.hotfixes.keys())
		self.assertNotIn('invalidProduct', self.hotfixes.keys())
		self.assertIn('tellstickDesktop', self.hotfixes.keys())

	def testRestart(self):
		self.assertFalse(self.__getHotFix('default')['restart'])
		self.assertFalse(self.__getHotFix('doNotRestart')['restart'])
		self.assertTrue(self.__getHotFix('doRestart')['restart'])

	def testScripts(self):
		self.assertFalse(self.__getHotFix('script')['applied'])

		self.assertFalse(os.path.exists('/tmp/tests/helloFromScript'))
		self.assertTrue(self.hotfixManager.apply('script'))
		self.assertTrue(os.path.exists('/tmp/tests/helloFromScript'))
		with open('/tmp/tests/helloFromScript', 'r') as fd:
			self.assertEqual(fd.read(), 'Hello World\n')
		os.remove('/tmp/tests/helloFromScript')

	def testSignature(self):
		self.assertFalse(self.__getHotFix('invalidSignature')['applied'])
		self.assertFalse(self.hotfixManager.apply('invalidSignature'))

	def testVersion(self):
		self.assertIn('default', self.hotfixes.keys())
		self.assertNotIn('version100', self.hotfixes.keys())
		self.assertIn('version123', self.hotfixes.keys())

	def __getHotFix(self, name):
		self.assertIn(name, self.hotfixes.keys())
		return self.hotfixes[name]
