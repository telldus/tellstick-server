# -*- coding: utf-8 -*-

from base import Plugin, implements
from tellduslive.base import ITelldusLiveObserver, TelldusLive
from gpio import Gpio
import socket, struct, fcntl

class Led(Plugin):
	implements(ITelldusLiveObserver)

	led2_red = 'ehrpwm.2:0'
	led2_green = 'ehrpwm.2:1'

	def __init__(self):
		self.gpio = Gpio(self.context)
		self.live = TelldusLive(self.context)
		# LED2
		self.gpio.initPWM(Led.led2_red)
		self.gpio.initPWM(Led.led2_green)
		self.setNetworkLed()

	def liveRegistered(self, msg):
		self.setNetworkLed()

	def liveDisconnected(self):
		self.setNetworkLed()

	def setNetworkLed(self):
		if Led.__getIp('eth0') == None:
			self.gpio.setPWM(Led.led2_red, freq=1, duty=50)
			return
		if self.live.isRegistered():
			self.gpio.setPWM(Led.led2_red, freq=100, duty=0)
			self.gpio.setPWM(Led.led2_green, freq=100, duty=50)
		else:
			self.gpio.setPWM(Led.led2_red, freq=100, duty=50)
			self.gpio.setPWM(Led.led2_green, freq=100, duty=0)

	@staticmethod
	def __getIp(iface):
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sockfd = sock.fileno()
		SIOCGIFADDR = 0x8915
		ifreq = struct.pack('16sH14s', iface, socket.AF_INET, '\x00'*14)
		try:
			res = fcntl.ioctl(sockfd, SIOCGIFADDR, ifreq)
		except:
			return None
		ip = struct.unpack('16sH2x4s8x', res)[2]
		return socket.inet_ntoa(ip)
