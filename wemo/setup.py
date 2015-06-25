#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
	from setuptools import setup
except ImportError:
	from distutils.core import setup

setup(
	name='WeMo',
	version='0.1',
	packages=['wemo'],
	package_dir = {'':'src'},
	entry_points={ \
		'telldus.startup': ['c = wemo:WeMo [cREQ]']
	},
	extras_require = dict(cREQ = 'Base>=0.1\nTelldus>=0.1'),
)
