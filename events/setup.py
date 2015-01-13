#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
	from setuptools import setup
except ImportError:
	from distutils.core import setup

setup(
	name='Events',
	version='0.1',
	packages=['events', 'events.base'],
	package_dir = {'':'src'},
	entry_points={ \
		'telldus.startup': ['c = events.base:EventManager [cREQ]']
	},
	extras_require = dict(cREQ = "Base>=0.1\nTelldusLive>=0.1")
)
