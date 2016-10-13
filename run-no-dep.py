#!/usr/bin/env python
# -*- coding: utf-8 -*-

plugins = {
	'telldus': ['DeviceManager', 'DeviceApiManager', 'React'],
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

if __name__ == "__main__":
	from base import Application

	p = loadClasses(plugins)
	s = loadClasses(startup)

	app = Application(run=False)
	app.run(startup=s)
