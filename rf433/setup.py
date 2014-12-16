#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
	name='RF433',
	version='0.1',
	packages=find_packages('src'),
	package_dir = {'':'src'},
	entry_points={ \
		'telldus.startup': ['c = rf433:RF433 [cREQ]'],
	},
	extras_require = dict(cREQ = 'Base>=0.1\nTelldus>=0.1\nTelldusLive>=0.1'),
	namespace_packages = ['rf433'],
	package_data={'rf433' : [
		'firmware/TellStickDuo.hex'
	]}
)
