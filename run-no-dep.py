#!/usr/bin/env python
# -*- coding: utf-8 -*-

import daemon
import errno
import getopt
import os
import signal
import sys
import time
from pwd import getpwnam
from grp import getgrnam

plugins = {
	'telldus': ['DeviceManager', 'DeviceApiManager'],
	'telldus.web': ['React'],
	'tellduslive.web': ['WebRequestHandler'],
	#PLUGINS#
}
startup = {
	'events.base': ['EventManager'],
	'group': ['Group'],
	'led': ['Led'],
	'log': ['Logger'],
	'rf433': ['RF433'],
	'scheduler.base': ['Scheduler'],
	'tellduslive.base': ['TelldusLive'],
	#STARTUP#
}

def loadClasses(cls):
	classes = []
	for module in cls:
		m = __import__(module, globals(), locals(), cls[module])
		for c in cls[module]:
			classes.append(getattr(m, c))
	return classes

def watchdog():
	def signalhandler(signum, frame):
		print("SIGTERM received")
		raise SystemExit("SIGTERM received")
	# Install signal handler
	signal.signal(signal.SIGTERM, signalhandler)
	while 1:
		clientPID = os.fork()
		if clientPID:
			print("Child started with PID %i" % clientPID)
			running = True
			exitCode = 0
			while running:
				try:
					(pid, exitCode) = os.waitpid(clientPID, 0)
					running = False
				except (KeyboardInterrupt, SystemExit):
					os.kill(clientPID, signal.SIGINT)
					(pid, exitCode) = os.waitpid(clientPID, 0)
					running = False
					exitCode = 0
				except OSError as error:
					if error.errno == errno.EINTR:
						os.kill(clientPID, signal.SIGINT)
					else:
						running = False
						exitCode = 0
				except Exception as error:
					print("Unknown exception", error)
					running = False
					exitCode = 0
			if exitCode == 0:
				print("Child exited successfully")
				sys.exit(0)
			else:
				print("Server crashed, restarting!")
				time.sleep(10)  # Don't flood
		else:
			main()

def main():
	from base import Application

	p = loadClasses(plugins)
	s = loadClasses(startup)

	app = Application(run=False)
	app.run(startup=s)

class PIDFile(object):
	def __init__(self):
		self.f = open('/var/run/tellstick-server.pid', 'w')

	def fileno(self):
		return self.f.fileno()

	def __enter__(self):
		self.f.write(str(os.getpid()))
		self.f.flush()

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.f.close()

if __name__ == "__main__":
	try:
		opts, args = getopt.getopt(sys.argv[1:], "n", ["nodaemon"])
	except getopt.GetoptError as exc:
		print(exc)
		sys.exit(2)

	daemonize = True
	for opt, arg in opts:
		if opt == '--nodaemon':
			daemonize = False

	pidfile = PIDFile()
	params = {
		'detach_process': True,
		'pidfile': pidfile,
		'uid': getpwnam('nobody').pw_uid,
		'gid': getgrnam('nogroup').gr_gid,
		'files_preserve': [pidfile]
	}
	if not daemonize:
		params['detach_process'] = False
		params['stdout'] = sys.stdout
		params['stderr'] = sys.stderr

	with daemon.DaemonContext(**params):
		if daemonize:
			watchdog()
		else:
			main()
