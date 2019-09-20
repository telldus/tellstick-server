# -*- coding: utf-8 -*-

import os
import unittest

from mock import patch

from ..UpgradeManager import HotFixManager, UpgradeManagerBase

class RebootException(Exception):
	pass

@staticmethod
def fetchVersion(__imageType):
	return '1.2.3'

def loadAppliedHotfixes(self):
	self.appliedHotfixes = []

@staticmethod
def reboot():
	raise RebootException()

def writeAppliedHotfixes(__self):
	pass

class HotFixManagerTest(unittest.TestCase):
	@patch.object(UpgradeManagerBase, 'fetchVersion', fetchVersion)
	@patch.object(HotFixManager, 'loadAppliedHotfixes', loadAppliedHotfixes)
	@patch.object(HotFixManager, 'writeAppliedHotfixes', writeAppliedHotfixes)
	def setUp(self):
		keyring = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'telldus.gpg'))
		UpgradeManagerBase.KEYRING = keyring
		HotFixManager.URL = 'https://fw.telldus.com/hotfixes/tests/testcases.yml'

		self.hotfixManager = HotFixManager()
		self.hotfixes = self.hotfixManager.list()

	def tearDown(self):
		files = [
			'/tmp/tests/helloworld',
			'/tmp/tests/helloFromScript',
		]
		for path in files:
			if os.path.exists(path):
				os.remove(path)

	def testApplied(self):
		self.assertFalse(self.__getHotFix('default')['applied'])
		self.hotfixManager.appliedHotfixes = ['default']
		self.hotfixManager.clearCache()
		self.hotfixes = self.hotfixManager.list()
		self.assertTrue(self.__getHotFix('default')['applied'])

	def testApply(self):
		self.assertFalse(self.hotfixManager.apply('unknown'))

		self.assertFalse(os.path.exists('/tmp/tests/helloworld'))
		self.assertTrue(self.hotfixManager.apply('helloworld'))
		self.assertTrue(os.path.exists('/tmp/tests/helloworld'))
		with open('/tmp/tests/helloworld', 'r') as fd:
			self.assertEqual(fd.read(), 'Hello World!\n')

	@patch.object(UpgradeManagerBase, 'reboot', reboot)
	def testApplyAll(self):
		autoHotfixes = ['default', 'deployAuto']
		manualHotfixes = ['deployMalformed', 'deployManual', 'helloworld']
		failedHotfixes = ['invalidSignature', 'scriptFailing']

		self.assertEqual(self.hotfixManager.appliedHotfixes, [])
		with self.assertRaises(RebootException):
			for name in self.hotfixManager.applyAll():
				# No manual hotfix may be applied
				self.assertNotIn(name, manualHotfixes)
		for name in autoHotfixes:
			# Make sure all auto has been appled
			self.assertIn(name, self.hotfixManager.appliedHotfixes)
		for name in failedHotfixes:
			# Make sure no failed has been marked as applied
			self.assertNotIn(name, self.hotfixManager.appliedHotfixes)

	def testDeployment(self):
		self.assertEqual(self.__getHotFix('default')['deployment'], 'auto')
		self.assertEqual(self.__getHotFix('deployAuto')['deployment'], 'auto')
		self.assertEqual(self.__getHotFix('deployManual')['deployment'], 'manual')
		self.assertEqual(self.__getHotFix('deployMalformed')['deployment'], 'manual')

	def testFiles(self):
		self.assertEqual(self.__getHotFix('invalidSourceFile')['files'], [])

	def testProducts(self):
		self.assertIn('default', list(self.hotfixes.keys()))
		self.assertNotIn('noProduct', list(self.hotfixes.keys()))
		self.assertNotIn('invalidProduct', list(self.hotfixes.keys()))
		self.assertIn('tellstickDesktop', list(self.hotfixes.keys()))

	@patch.object(UpgradeManagerBase, 'reboot', reboot)
	def testRestart(self):
		self.assertFalse(self.__getHotFix('default')['restart'])
		self.assertFalse(self.__getHotFix('doNotRestart')['restart'])
		self.assertTrue(self.__getHotFix('doRestart')['restart'])
		with self.assertRaises(RebootException):
			self.hotfixManager.apply('doRestart')
		try:
			self.hotfixManager.apply('default')
			self.hotfixManager.apply('doNotRestart')
		except RebootException:
			self.fail('Hotfix tried to reboot that shouldn\'t')

	def testScripts(self):
		self.assertFalse(self.__getHotFix('script')['applied'])
		self.assertFalse(os.path.exists('/tmp/tests/helloFromScript'))
		self.assertTrue(self.hotfixManager.apply('script'))
		self.assertTrue(os.path.exists('/tmp/tests/helloFromScript'))
		with open('/tmp/tests/helloFromScript', 'r') as fd:
			self.assertEqual(fd.read(), 'Hello World\n')
		self.assertTrue(self.__getHotFix('script')['applied'])

		self.assertFalse(self.__getHotFix('scriptFailing')['applied'])
		self.assertFalse(self.hotfixManager.apply('scriptFailing'))
		self.assertFalse(self.__getHotFix('scriptFailing')['applied'])

	def testSignature(self):
		self.assertFalse(self.__getHotFix('invalidSignature')['applied'])
		self.assertFalse(self.hotfixManager.apply('invalidSignature'))

	def testVersion(self):
		self.assertIn('default', list(self.hotfixes.keys()))
		self.assertNotIn('version100', list(self.hotfixes.keys()))
		self.assertIn('version123', list(self.hotfixes.keys()))

	def __getHotFix(self, name):
		self.assertIn(name, list(self.hotfixes.keys()))
		return self.hotfixes[name]
