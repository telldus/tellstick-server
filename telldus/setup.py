#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
	name='Telldus',
	version='0.1',
	packages=find_packages('src'),
	package_dir = {'':'src'},
	extras_require = {
		'telldus': ['Base>=0.1'],
	}
)
