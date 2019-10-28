#!/usr/bin/env python3
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
		mod = __import__(module, globals(), locals(), cls[module])
		for c in cls[module]:
			classes.append(getattr(mod, c))
	return classes

def watchdog():
	def signalhandler(signum, frame):
		del signum, frame
		print("SIGTERM received")
		raise SystemExit("SIGTERM received")
	# Install signal handler
	signal.signal(signal.SIGTERM, signalhandler)
	while 1:
		clientPID = os.fork()
		if clientPID:
			print(f"Child started with PID {clientPID}")
			running = True
			exitCode = 0
			while running:
				try:
					(pid, exitCode) = os.waitpid(clientPID, 0)
					del pid
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
					print(f"Unknown exception {error}")
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

	loadClasses(plugins)
	startupClasses = loadClasses(startup)

	app = Application(run=False)
	app.run(startup=startupClasses)

class PIDFile(object):  # pylint: disable=too-few-public-methods
	def __init__(self):
		self.fd = open('/var/run/tellstick-server.pid', 'w')

	def fileno(self):
		return self.fd.fileno()

	def __enter__(self):
		self.fd.write(str(os.getpid()))
		self.fd.flush()

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.fd.close()

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
		'pidfile': pidfile,
		'files_preserve': [pidfile],
	}
	if daemonize:
		params['detach_process'] = True
		params['uid'] = getpwnam('nobody').pw_uid
		params['gid'] = getgrnam('nogroup').gr_gid
	else:
		params['detach_process'] = False
		params['stdout'] = sys.stdout
		params['stderr'] = sys.stderr

	with daemon.DaemonContext(**params):
		if daemonize:
			watchdog()
		else:
			main()
