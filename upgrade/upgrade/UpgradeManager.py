#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import getopt
import hashlib
import os
import platform
import sys
import time
import subprocess
import xml.parsers.expat

from six.moves import http_client, urllib

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
			conn.request('GET', '/versions.xml')
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
	opts, __args = getopt.getopt(sys.argv[1:], "", ["check", "monitor", "upgrade"])
	upgradeManager = UpgradeManager()

	check = False
	upgrade = False
	monitor = False
	for opt, __arg in opts:
		if opt in ("--check"):
			check = True
		if opt in ("--upgrade"):
			upgrade = True
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
