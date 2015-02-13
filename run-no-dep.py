#!/usr/bin/env python
# -*- coding: utf-8 -*-

plugins = {
	'telldus': ['DeviceManager'],
	'zwave.workaround': ['WorkaroundPlugin'],
}
startup = {
	'led': ['Led'],
	'log': ['Logger'],
	'scheduler.base': ['Scheduler'],
	'tellduslive.base': ['TelldusLive'],
	'zwave.telldus': ['TelldusZWave'],
}

def loadClasses(cls):
	classes = []
	for module in cls:
		m = __import__(module, globals(), locals(), cls[module])
		for c in cls[module]:
			classes.append(getattr(m, c))
	return classes

if __name__ == "__main__":
	from base import Application

	p = loadClasses(plugins)
	s = loadClasses(startup)

	app = Application(run=False)
	app.run(startup=s)
