#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import getopt
import hashlib
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
import xml.parsers.expat

from six.moves import http_client, urllib
import yaml

from board import Board

class UpgradeManagerBase(object):
	KEYRING = '/etc/upgrade/telldus.gpg'

	@staticmethod
	def downloadFile(url, downloadFilename, size=None):
		try:
			urlRequest = urllib.request.urlopen(url)
		except Exception as error:
			logging.error("Error downloading: %s", error)
			return False
		meta = urlRequest.info()
		fileSize = int(meta.getheaders("Content-Length")[0])
		if size is not None and fileSize != size:
			logging.error("Size mismatch %s!=%s", fileSize, size)
			return False
		logging.info("Downloading bytes: %s", (fileSize))
		fd = open(downloadFilename, 'wb')
		fileSizeDl = 0
		blockSz = 8192
		while True:
			buff = urlRequest.read(blockSz)
			if not buff:
				break
			fileSizeDl += len(buff)
			fd.write(buff)
			status = "%10d  [%3.2f%%]\r" % (fileSizeDl, fileSizeDl * 100. / fileSize)
			sys.stdout.write(status)
			sys.stdout.flush()
		fd.close()
		return True

	@staticmethod
	def fetchVersion(imageType):
		if imageType == 'firmware':
			with open('/etc/builddate') as fd:
				return fd.readline().strip()
		if imageType == 'kernel':
			return platform.release()
		if imageType == 'u-boot':
			with open('/proc/cmdline') as fd:
				for value in fd.readline().split(' '):
					parts = value.strip().split('=')
					if len(parts) < 2:
						continue
					if parts[0] == 'ubootver':
						return parts[1]
				return None
		return None

	@staticmethod
	def reboot():
		subprocess.call('/sbin/reboot')

	@staticmethod
	def verifyFile(path, size=None, checksum=None):
		if size is not None and os.stat(path).st_size != size:
			logging.error("Downloaded filesize doesn't match recorded size")
			return False
		if checksum is not None:
			sha1 = hashlib.sha1()
			fd = open(path, 'rb')
			try:
				sha1.update(fd.read())
			finally:
				fd.close()
			if sha1.hexdigest() != checksum:
				logging.error("Checksum mismatch %s!=%s", sha1.hexdigest(), checksum)
				return False
		# Check signature
		retval = subprocess.call(['gpg',
			'--verify',
			'--no-default-keyring',
			'--keyring', UpgradeManagerBase.KEYRING,
			'%s.asc' % path
			])
		if retval != 0:
			logging.error("Could not verify signature")
			return False
		logging.info("File verified successfully")
		return True

class HotFixManager(UpgradeManagerBase):
	URL = 'https://fw.telldus.com/hotfixes.yml'
	APPLIED_FILE = '/etc/upgrade/hotfixes'

	def __init__(self):
		self.url = urllib.parse.urlparse(HotFixManager.URL)
		self.appliedHotfixes = None
		self.hotfixes = None  # Cache the list

	def apply(self, name):
		hotfixes = self.list()
		if name not in hotfixes:
			return False
		hotfix = hotfixes[name]
		try:
			files = []
			targets = {}
			scripts = []
			# Download files
			for hotfixFile in hotfix['files']:
				__fd, filename = tempfile.mkstemp()
				files.append(filename)
				targets[filename] = hotfixFile['target']
				if not self.downloadFile(hotfixFile['source'], filename):
					return False
				signature = '%s.asc' % filename
				if not self.downloadFile('%s.asc' % hotfixFile['source'], signature):
					return False
				files.append(signature)
				if not self.verifyFile(filename):
					return False

			# Download scripts
			for hotfixFile in hotfix['scripts']:
				fd, filename = tempfile.mkstemp()
				files.append(filename)
				if not self.downloadFile(hotfixFile['source'], filename):
					return False
				signature = '%s.asc' % filename
				if not self.downloadFile('%s.asc' % hotfixFile['source'], signature):
					return False
				files.append(signature)
				if not self.verifyFile(filename):
					return False
				os.close(fd)
				os.chmod(filename, 0o744)
				scripts.append(filename)

			# Copy files
			for source, target in targets.items():
				directory = os.path.dirname(target)
				if not os.path.exists(directory):
					os.makedirs(directory)
				shutil.move(source, target)

			# Run scripts
			for script in scripts:
				retval = subprocess.call(script)
				if retval != 0:
					# Script failed. No not continue. Let this script run again.
					return False

		finally:
			# Cleanup of downloaded files
			for filename in files:
				if os.path.exists(filename):
					os.remove(filename)
		self.appliedHotfixes.append(name)
		self.hotfixes[name]['applied'] = True
		self.writeAppliedHotfixes()
		if hotfix['restart']:
			self.reboot()
		return True

	def applyAll(self):
		for name, hotfix in self.list().items():
			if hotfix['applied']:
				continue
			if hotfix['deployment'] != 'auto':
				continue
			yield name
			self.apply(name)

	def clearCache(self):
		self.hotfixes = None

	def list(self):
		if isinstance(self.hotfixes, dict):
			return self.hotfixes
		self.hotfixes = {}
		conn = http_client.HTTPSConnection(self.url.netloc)
		try:
			conn.request('GET', self.url.path)
			response = conn.getresponse()
		except Exception as error:
			logging.warning("Could not get hotfix list: %s", error)
			return {}
		hotfixes = yaml.load(response)
		for name in hotfixes:
			if not HotFixManager.isHotfixValid(hotfixes[name]):
				continue
			self.hotfixes[name] = self.processHotfix(name, hotfixes[name])
		return self.hotfixes

	def processHotfix(self, name, hotfixInfo):
		files = []
		scripts = []
		base = hotfixInfo.get('base', '/')
		if base[0] != '/':
			base = '/%s' % base
		path = os.path.dirname(self.url.path)
		if path == '/':
			path = ''
		elif path[0] != '/':
			path = '/%s' % path
		for fileInfo in hotfixInfo.get('files', []):
			source = fileInfo.get('source', '')
			target = fileInfo.get('target', '')
			if source is '' or target is '':
				continue
			if source[0] != '/':
				source = '/%s' % source
			source = '%s://%s%s%s%s' % (
				self.url.scheme,
				self.url.netloc,
				path,
				base,
				source
			)
			files.append({
				'source': source,
				'target': target,
			})
		for fileInfo in hotfixInfo.get('scripts', []):
			if isinstance(fileInfo, dict):
				source = fileInfo.get('source', '')
			else:
				source = fileInfo
			if source is '':
				continue
			if source[0] != '/':
				source = '/%s' % source
			source = '%s://%s%s%s%s' % (
				self.url.scheme,
				self.url.netloc,
				path,
				base,
				source
			)
			scripts.append({
				'source': source,
			})
		deployment = 'manual' if hotfixInfo.get('deployment', 'auto') != 'auto' else 'auto'
		return {
			'applied': self.isHotfixApplied(name),
			'files': files,
			'deployment': deployment,
			'restart': hotfixInfo.get('restart', False),
			'scripts': scripts,
		}

	def isHotfixApplied(self, name):
		if self.appliedHotfixes is None:
			self.loadAppliedHotfixes()
		return name in self.appliedHotfixes

	def loadAppliedHotfixes(self):
		self.appliedHotfixes = []
		if not os.path.exists(HotFixManager.APPLIED_FILE):
			return
		with open(HotFixManager.APPLIED_FILE, 'r') as fd:
			self.appliedHotfixes = [line.strip() for line in fd]

	def writeAppliedHotfixes(self):
		with open(HotFixManager.APPLIED_FILE, 'w') as fd:
			fd.write('\n'.join(self.appliedHotfixes))
			fd.write('\n')

	@staticmethod
	def isHotfixValid(hotfixInfo):
		if 'version' in hotfixInfo:
			if hotfixInfo['version'] != UpgradeManagerBase.fetchVersion('firmware'):
				return False
		if 'products' in hotfixInfo:
			products = hotfixInfo['products']
			if not isinstance(products, list):
				return False  # Malformed hotfix
			if Board.product() not in products:
				# Hotfix not for this board
				return False
		return True

class UpgradeManager(UpgradeManagerBase):
	def __init__(self):
		self._filename = False
		self._firmwareType = None
		self._queue = []
		self._product = None
		self._dist = None
		self._content = ''
		self._attrs = None
		self._url = ''

	def check(self):
		conn = http_client.HTTPConnection('fw.telldus.com:80')
		try:
			conn.request('GET', "/versions.xml?mac=%s&hw=%s&product=%s" % (Board.getMacAddr(), self.hw(), Board.product()))
			response = conn.getresponse()
		except Exception as error:
			logging.warning("Could not get version info: %s", error)
			return False
		parser = xml.parsers.expat.ParserCreate()

		parser.StartElementHandler = self._startElement
		parser.EndElementHandler = self._endElement
		parser.CharacterDataHandler = self._characterDataHandler
		parser.Parse(response.read())
		if self._url != '':
			return True
		return False

	def checkForUpgrade(self, element, attrs):
		if 'name' not in self._product or 'hw' not in self._product:
			return
		if self._product['name'] != Board.product() or self._product['hw'] != self.hw():
			return
		if 'name' not in self._dist or 'version' not in attrs:
			return
		if self._dist['name'] != self.distribution():
			return
		version = self.fetchVersion(element)
		if version is None:
			return
		if attrs['version'] == version:
			logging.info("%s up to date", element)
			return
		logging.warning("Do upgrade %s", element)
		if element in ['firmware', 'kernel', 'u-boot']:
			self._attrs = attrs
			self._url = self._content
			self._firmwareType = element

	@staticmethod
	def distribution():
		with open('/etc/distribution') as fd:
			return fd.readline().strip()

	def download(self):
		attrs = self._attrs
		url = self._url
		if 'size' not in attrs or 'sha1' not in attrs:
			return (None, None)
		urlsplit = urllib.parse.urlsplit(url)
		targetFilename = os.path.basename(urlsplit.path)
		downloadDir = Board.firmwareDownloadDir() + '/download/'
		downloadFilename = downloadDir + targetFilename
		if not os.path.exists(downloadDir):
			os.makedirs(downloadDir)
		try:
			# Make sure there is enough free space
			with open('/proc/sys/vm/drop_caches', 'w') as fd:
				fd.write('3')
		except Exception as __error:
			pass
		stat = os.statvfs(downloadDir)
		freeSpace = stat.f_frsize * stat.f_bavail
		if int(attrs['size']) > freeSpace:
			logging.error("Not enough RAM to download image")
			return (None, None)

		if not self.downloadFile(url, downloadFilename, size=int(attrs['size'])):
			return (None, None)
		if not self.downloadFile('%s.asc' % url, '%s.asc' % downloadFilename):
			os.remove(downloadFilename)
			return (None, None)
		if not self.verifyFile(downloadFilename, int(attrs['size']), attrs['sha1']):
			os.remove(downloadFilename)
			os.remove('%s.asc' % downloadFilename)
			return (None, None)
		os.remove('%s.asc' % downloadFilename)
		return (self._firmwareType, downloadFilename)

	@staticmethod
	def hw():
		return Board.product() if Board.hw() == 'tellstick' else Board.hw()

	def _characterDataHandler(self, character):
		self._content = self._content + character

	def _startElement(self, name, attrs):
		self._queue.append((name, attrs))
		if name == 'product':
			self._product = attrs
			return
		if self._product is None:
			return
		if name == 'dist':
			self._dist = attrs
			return
		if self._dist is None:
			return

	def _endElement(self, name):
		(element, attrs) = self._queue.pop()
		self._content = self._content.strip()
		if element != name:
			logging.error("Error!")
		if name == 'product':
			self._product = None
		if name == 'dist':
			self._dist = None
		if name in ['firmware', 'kernel', 'u-boot']:
			self.checkForUpgrade(element, attrs)
		self._content = ''

def runCli():
	logging.getLogger().setLevel(logging.INFO)
	opts, __args = getopt.getopt(sys.argv[1:], "", [
		"check",
		"hotfix=",
		"monitor",
		"upgrade"
	])
	upgradeManager = UpgradeManager()

	check = False
	hotfix = ''
	upgrade = False
	monitor = False
	for opt, arg in opts:
		if opt in ("--check"):
			check = True
		if opt in ("--upgrade"):
			upgrade = True
		if opt in ("--hotfix"):
			hotfix = arg
		if opt in ("--monitor"):
			monitor = True
			break

	if monitor:
		while True:
			try:
				if not upgradeManager.check():
					logging.info("Sleep for one day")
					time.sleep(60*60*24)
					continue
				(fwType, filename) = upgradeManager.download()
				if fwType is None:
					raise Exception("Error downloading file")
				Board.doUpgradeImage(fwType, filename)
				logging.info("Sleep for one day")
				time.sleep(60*60*24)
			except KeyboardInterrupt:
				logging.info("Exit")
				sys.exit(0)
			except Exception as error:
				logging.warning("Could not fetch. Sleep one minute and try again")
				logging.warning(str(error))
				time.sleep(60)

	if hotfix:
		hotfixManager = HotFixManager()
		if hotfix == 'list':
			for hotfixName, hfix in hotfixManager.list().items():
				sys.stdout.write('%s %s\n' % ('*' if hfix['applied'] else ' ', hotfixName))
			sys.stdout.flush()
			sys.exit(0)
		if hotfix == 'all':
			for hotfixName in hotfixManager.applyAll():
				logging.warning('Applying %s', hotfixName)
			sys.exit(0)
		if hotfix not in hotfixManager.list():
			logging.error('Hotfix %s not found', hotfix)
			sys.exit(1)
		if hotfixManager.isHotfixApplied(hotfix):
			logging.error('Hotfix %s already applied', hotfix)
			sys.exit(1)
		logging.warning('Applying %s', hotfix)
		if hotfixManager.apply(hotfix):
			sys.exit(0)
		sys.exit(1)

	if check:
		if upgradeManager.check():
			sys.exit(1)
		else:
			sys.exit(0)

	if upgrade:
		if not upgradeManager.check():
			sys.exit(0)
		(fwType, filename) = upgradeManager.download()
		if fwType is None:
			sys.exit(1)
		Board.doUpgradeImage(fwType, filename)

	sys.exit(0)

if __name__ == '__main__':
	runCli()
