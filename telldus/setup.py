#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
	from setuptools import setup
except ImportError:
	from distutils.core import setup

setup(
	name='Telldus',
	version='0.1',
	packages=['telldus'],
	package_dir = {'':'src'},
	entry_points={ \
		'telldus.plugins': [
			'api = telldus.DeviceApiManager',
			'react = telldus.React'
		]
	},
	extras_require = {
		'telldus': ['Base>=0.1\nEvent>=0.1'],
	},
	package_data={'telldus' : [
		'templates/*.html',
		'htdocs/img/*.png',
		'htdocs/img/*.ico',
		'htdocs/js/*.js',
	]}
)
