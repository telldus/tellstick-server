#!/usr/bin/env python3
# -*- coding: utf-8 -*-

try:
	from setuptools import setup
except ImportError:
	from distutils.core import setup

setup(
	name='ZWave',
	version='0.1',
	packages=['zwave'],
	entry_points={ \
		'telldus.startup': ['c = zwave:Manager [cREQ]'],
	},
	extras_require=dict(cREQ='Base>=0.1\nBoard>=0.1\nTelldus>=0.1'),
)
