#!/usr/bin/env python3
# -*- coding: utf-8 -*-

try:
	from setuptools import setup
except ImportError:
	from distutils.core import setup

setup(
	name='Led',
	version='0.1',
	packages=['led'],
	package_dir = {'':'src'},
	entry_points={ \
		'telldus.startup': ['c = led:Led [cREQ]']
	},
	extras_require = dict(cREQ = 'Base>=0.1\nGPIO>=0.1\nTelldusLive>=0.1'),
)
