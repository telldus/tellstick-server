#!/usr/bin/env python
# -*- coding: utf-8 -*-

import hashlib, httplib, random, os, time
import platform, urllib2, urlparse
import xml.parsers.expat
from datetime import datetime, timedelta
from board import Board

class UpgradeManager(object):
	def __init__(self):
		self._filename = False
		self._queue = []
		self._product = None
		self._dist = None
		self._content = ''
		self._requireRestart = False

	def check(self):
		conn = httplib.HTTPConnection("api.telldus.net:80")
		conn.request('GET', "/client/versions")
		response = conn.getresponse()

		p = xml.parsers.expat.ParserCreate()

		p.StartElementHandler = self._startElement
		p.EndElementHandler = self._endElement
		p.CharacterDataHandler = self._characterDataHandler
		p.Parse(response.read())
		if self._requireRestart:
			return True
		return False

	def checkForUpgrade(self, el, attrs):
		if 'name' not in self._product or 'hw' not in self._product:
			return
		if self._product['name'] != Board.product() or self._product['hw'] != Board.hw():
			return
		if 'name' not in self._dist or 'version' not in attrs:
			return
		if self._dist['name'] != self.distribution():
			return
		version = self.fetchVersion(el)
		if version is None:
			return
		if attrs['version'] == version:
			print el, "up to date"
			return
		print "Do upgrade", el
		if el == 'firmware':
			self._filename = self.doUpgrade(attrs, self._content)
		if el == 'kernel':
			self._filename = self.doUpgrade(attrs, self._content)
		if self._filename != False:
			self._firmwareType = el
			self._requireRestart = True
			return

	def fetchVersion(self, imageType):
		if imageType == 'firmware':
			with open('/etc/builddate') as f:
				return f.readline().strip()
		if imageType == 'kernel':
			return platform.release()
		return None

	def distribution(self):
		with open('/etc/distribution') as f:
			return f.readline().strip()

	def doUpgrade(self, attrs, url):
		if 'size' not in attrs or 'sha1' not in attrs:
			return False
		urlsplit = urlparse.urlsplit(url)
		targetFilename = os.path.basename(urlsplit.path)
		downloadDir = Board.firmwareDownloadDir() + '/download/'
		downloadFilename = downloadDir + targetFilename
		if not os.path.exists(downloadDir):
			os.makedirs(downloadDir)
		# Make sure there is enough free space
		with open('/proc/sys/vm/drop_caches', 'w') as f:
				f.write('3')
		s = os.statvfs(downloadDir)
		freeSpace = s.f_frsize * s.f_bavail
		if int(attrs['size']) > freeSpace:
			print "Not enough RAM to download image"
			return False
		u = urllib2.urlopen(url)
		meta = u.info()
		fileSize = int(meta.getheaders("Content-Length")[0])
		if fileSize != int(attrs['size']):
			print "Size mismatch", fileSize, int(attrs['size'])
			return False
		print "Downloading bytes: %s" % (fileSize)
		f = open(downloadFilename, 'wb')
		fileSizeDl = 0
		blockSz = 8192
		while True:
			buffer = u.read(blockSz)
			if not buffer:
					break
			fileSizeDl += len(buffer)
			f.write(buffer)
			status = "%10d  [%3.2f%%]\r" % (fileSizeDl, fileSizeDl * 100. / fileSize)
			print status,
		f.close()
		if not self.verifyFile(downloadFilename, int(attrs['size']), attrs['sha1']):
			os.remove(downloadFilename)
			return False
		return downloadFilename

	def upgradeLater(self):
		starttime = datetime.utcnow().replace(hour=0,minute=0,second=0,microsecond=0)
		if datetime.utcnow() > (starttime + timedelta(hours=4)):
			starttime = starttime + timedelta(days=1)
		reboottime = starttime + timedelta(minutes=random.randint(0,240))
		while datetime.utcnow() < reboottime:
			time.sleep(300)
		Board.doUpgradeImage(self._firmwareType, self._filename)

	def verifyFile(self, filename, size, checksum):
		if os.stat(filename).st_size != size:
			print "Downloaded filesize doesn't match recorded size"
			return False
		sha1 = hashlib.sha1()
		f = open(filename, 'rb')
		try:
			sha1.update(f.read())
		finally:
			f.close()
		if sha1.hexdigest() != checksum:
			print "Checksum mismatch", sha1.hexdigest(), checksum
			return False
		return True

	def _characterDataHandler(self, c):
		self._content = self._content + c

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
		(el, attrs) = self._queue.pop()
		self._content = self._content.strip()
		if el != name:
			print "Error!"
		if name == 'product':
			self._product = None
		if name == 'dist':
			self._dist = None
		if name in ['firmware', 'kernel']:
			self.checkForUpgrade(el, attrs)
		self._content = ''

if __name__ == '__main__':
	um = UpgradeManager()
	while True:
		try:
			if um.check():
				print "Reboot tonight"
				um.upgradeLater()
			print "Sleep for one day"
			time.sleep(60*60*24)
		except KeyboardInterrupt:
			print "Exit"
			break
		except Exception as e:
			print "Could not fetch. Sleep one minute and try again"
			print str(e)
			time.sleep(60)
