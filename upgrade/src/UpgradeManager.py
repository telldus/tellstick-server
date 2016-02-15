#!/usr/bin/env python
# -*- coding: utf-8 -*-

import getopt, hashlib, httplib, os, sys, time
import platform, urllib2, urlparse
import xml.parsers.expat
import gnupg
from board import Board

class UpgradeManager(object):
	def __init__(self):
		self._filename = False
		self._queue = []
		self._product = None
		self._dist = None
		self._content = ''
		self._attrs = None
		self._url = ''

	def check(self):
		conn = httplib.HTTPConnection('fw.telldus.com:80')
		try:
			conn.request('GET', '/versions.xml')
			response = conn.getresponse()
		except:
			print "Could not get version info"
			return False

		p = xml.parsers.expat.ParserCreate()

		p.StartElementHandler = self._startElement
		p.EndElementHandler = self._endElement
		p.CharacterDataHandler = self._characterDataHandler
		p.Parse(response.read())
		if self._url != '':
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
		if el in ['firmware', 'kernel', 'u-boot']:
			self._attrs = attrs
			self._url = self._content
			self._firmwareType = el

	def fetchVersion(self, imageType):
		if imageType == 'firmware':
			with open('/etc/builddate') as f:
				return f.readline().strip()
		if imageType == 'kernel':
			return platform.release()
		if imageType == 'u-boot':
			with open('/proc/cmdline') as f:
				for v in f.readline().split(' '):
					args = v.strip().split('=')
					if len(args) < 2:
						continue
					if args[0] == 'ubootver':
						return args[1]
				return None
		return None

	def distribution(self):
		with open('/etc/distribution') as f:
			return f.readline().strip()

	def download(self):
		attrs = self._attrs
		url = self._url
		if 'size' not in attrs or 'sha1' not in attrs:
			return (None, None)
		urlsplit = urlparse.urlsplit(url)
		targetFilename = os.path.basename(urlsplit.path)
		downloadDir = Board.firmwareDownloadDir() + '/download/'
		downloadFilename = downloadDir + targetFilename
		if not os.path.exists(downloadDir):
			os.makedirs(downloadDir)
		try:
			# Make sure there is enough free space
			with open('/proc/sys/vm/drop_caches', 'w') as f:
					f.write('3')
		except:
			pass
		s = os.statvfs(downloadDir)
		freeSpace = s.f_frsize * s.f_bavail
		if int(attrs['size']) > freeSpace:
			print "Not enough RAM to download image"
			return (None, None)

		if not self._downloadFile(url, downloadFilename, size=int(attrs['size'])):
			return (None, None)
		if not self._downloadFile('%s.asc' % url, '%s.asc' % downloadFilename):
			os.remove(downloadFilename)
			return (None, None)
		if not self.verifyFile(downloadFilename, int(attrs['size']), attrs['sha1']):
			os.remove(downloadFilename)
			os.remove('%s.asc' % downloadFilename)
			return (None, None)
		os.remove('%s.asc' % downloadFilename)
		return (self._firmwareType, downloadFilename)

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
		# Check signature
		gpg = gnupg.GPG(keyring='/etc/upgrade/telldus.gpg')
		v = gpg.verify_file(open(filename), '%s.asc' % filename)
		if v.valid is not True:
			print "Could not verify signature:", v.status
			return False
		print "File verified successfully"
		return True

	def _characterDataHandler(self, c):
		self._content = self._content + c

	def _downloadFile(self, url, downloadFilename, size=None):
		try:
			u = urllib2.urlopen(url)
		except Exception as e:
			print "Error downloading:", e
			return False
		meta = u.info()
		fileSize = int(meta.getheaders("Content-Length")[0])
		if size is not None and fileSize != size:
			print "Size mismatch", fileSize, size
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
		return True

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
		if name in ['firmware', 'kernel', 'u-boot']:
			self.checkForUpgrade(el, attrs)
		self._content = ''

if __name__ == '__main__':
	opts, args = getopt.getopt(sys.argv[1:], "", ["check","monitor","upgrade"])
	um = UpgradeManager()

	check = False
	upgrade = False
	monitor = False
	for opt, arg in opts:
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
				if not um.check():
					print "Sleep for one day"
					time.sleep(60*60*24)
					continue
				(type, filename) = um.download()
				if type is None:
					raise Exception("Error downloading file")
				Board.doUpgradeImage(type, filename)
				print "Sleep for one day"
				time.sleep(60*60*24)
			except KeyboardInterrupt:
				print "Exit"
				sys.exit(0)
			except Exception as e:
				print "Could not fetch. Sleep one minute and try again"
				print str(e)
				time.sleep(60)

	if check:
		if um.check():
			sys.exit(1)
		else:
			sys.exit(0)

	if upgrade:
		if not um.check():
			sys.exit(0)
		(type, filename) = um.download()
		if type is None:
			sys.exit(1)
		Board.doUpgradeImage(type, filename)

	sys.exit(0)
