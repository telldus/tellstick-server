#!/usr/bin/env python
# -*- coding: utf-8 -*-

import hashlib, httplib, os, time
import platform, urllib2
import xml.parsers.expat

PRODUCT = 'tellstick-znet'
HW = '1'
TARGET_DIR = '/var/firmware'

class UpgradeManager(object):
	def __init__(self):
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
			print "Restart"
			os.system("/sbin/reboot")

	def checkForUpgrade(self, el, attrs):
		if 'name' not in self._product or 'hw' not in self._product:
			return
		if self._product['name'] != PRODUCT or self._product['hw'] != HW:
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
		if el == 'firmware' and self.doUpgrade(attrs, self._content, 'core-image-tellstick-beagleboard.ubi'):
			self._requireRestart = True
			return
		if el == 'kernel' and self.doUpgrade(attrs, self._content, 'uImage'):
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

	def doUpgrade(self, attrs, url, targetFilename):
		if 'size' not in attrs or 'sha1' not in attrs:
			return False
		downloadDir = TARGET_DIR + '/download/'
		downloadFilename = downloadDir + targetFilename
		if not os.path.exists(downloadDir):
			os.makedirs(downloadDir)
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
		os.rename(downloadFilename, TARGET_DIR + '/' + targetFilename)
		return True

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
			um.check()
			print "Sleep for one day"
			time.sleep(60*60*24)
		except KeyboardInterrupt:
			print "Exit"
			break
		except:
			print "Could not fetch. Sleep one minute and try again"
			time.sleep(60)
