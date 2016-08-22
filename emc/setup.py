#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
	from setuptools import setup
except ImportError:
	from distutils.core import setup

setup(
	name='EMC',
	version='0.1',
	packages=['emc'],
	package_dir = {'':'src'},
	entry_points={ \
		'telldus.startup': ['c = emc:Emc [cREQ]']
	},
	extras_require = dict(cREQ = 'Base>=0.1\nRF433>=0.1\nZWave>=0.1'),
)
