#!/usr/bin/env python3
# -*- coding: utf-8 -*-

try:
	from setuptools import setup
except ImportError:
	from distutils.core import setup

setup(
	name='TelldusCore',
	version='0.1',
	packages=['tellduscore'],
	package_dir = {'':'src'},
	entry_points={ \
		'telldus.startup': ['c = tellduscore:TelldusCore']
	},
)
