#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
	from setuptools import setup
except ImportError:
	from distutils.core import setup

setup(
	name='Logger',
	version='0.1',
	packages=['log'],
	package_dir = {'':'src'},
	entry_points={ \
		'telldus.startup': ['c = log:Logger [cREQ]']
	},
	extras_require = dict(cREQ = "Base>=0.1")
)
