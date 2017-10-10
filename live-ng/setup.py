#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
	from setuptools import setup
except ImportError:
	from distutils.core import setup

setup(
	name='Telldus Live NG',
	version='0.1',
	packages=['tellduslive_ng'],
	entry_points={ \
		'telldus.startup': ['c = tellduslive_ng:Manager [cREQ]']
	},
	extras_require=dict(cREQ='Base>=0.1\nTelldus>=0.1'),
)
