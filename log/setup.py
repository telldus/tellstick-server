#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
	name='Logger',
	version='0.1',
	packages=find_packages('src'),
	package_dir = {'':'src'},
	entry_points={ \
		'telldus.startup': ['c = log:Logger [cREQ]']
	},
	extras_require = dict(cREQ = "Base>=0.1")
)
