#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
	from setuptools import setup
except ImportError:
	from distutils.core import setup

setup(
	name='TelldusLive',
	version='0.1',
	packages=['tellduslive', 'tellduslive.base'],
	package_dir = {'':'src'},
	entry_points={ \
		'telldus.startup': ['c = tellduslive.base:TelldusLive [cREQ]']
	},
	extras_require = dict(cREQ = "Base>=0.1")
)
