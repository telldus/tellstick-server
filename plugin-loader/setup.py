#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
	from setuptools import setup
except ImportError:
	from distutils.core import setup

setup(
	name='Plugin loader',
	version='0.1',
	packages=['pluginloader'],
	package_dir = {'':'src'},
	entry_points={ \
		'telldus.startup': ['c = pluginloader:Loader [cREQ]']
	},
	extras_require = dict(cREQ = 'Base>=0.1'),
)
