#!/usr/bin/env python3
# -*- coding: utf-8 -*-

try:
	from setuptools import setup
except ImportError:
	from distutils.core import setup

setup(
	name='TelldusLive',
	version='0.1',
	packages=['tellduslive', 'tellduslive.base', 'tellduslive.web'],
	package_dir = {'':'src'},
	entry_points={ \
		'telldus.startup': ['c = tellduslive.base:TelldusLive [cREQ]'],
		'telldus.plugins': ['c = tellduslive.web:WebRequestHandler']
	},
	extras_require = dict(cREQ = "Base>=0.1"),
	package_data={'tellduslive' : [
		'web/templates/*.html',
	]}
)
