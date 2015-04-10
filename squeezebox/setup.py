#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
	from setuptools import setup
except ImportError:
	from distutils.core import setup

setup(
	name='SqueezeBox',
	version='0.1',
	packages=['squeezebox'],
	package_dir = {'':'src'},
	entry_points={ \
		'telldus.startup': ['c = squeezebox:SqueezeBox [cREQ]']
	},
	extras_require = dict(cREQ = 'Base>=0.1\nTelldus>=0.1'),
)
