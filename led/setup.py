#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
	name='Led',
	version='0.1',
	packages=find_packages('src'),
	package_dir = {'':'src'},
	entry_points={ \
		'telldus.startup': ['c = led:Led [cREQ]']
	},
	extras_require = dict(cREQ = 'Base>=0.1\nGPIO>=0.1\nTelldusLive>=0.1'),
)
