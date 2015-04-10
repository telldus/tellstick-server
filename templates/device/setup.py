#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
	from setuptools import setup
except ImportError:
	from distutils.core import setup

setup(
	name='Dummy device',
	version='0.1',
	packages=['dummy'],
	package_dir = {'':'src'},
	entry_points={ \
		'telldus.startup': ['c = dummy:Dummy [cREQ]']
	},
	extras_require = dict(cREQ = 'Base>=0.1\nTelldus>=0.1'),
)
