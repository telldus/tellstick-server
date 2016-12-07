#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
	from setuptools import setup
except ImportError:
	from distutils.core import setup

setup(
	name='API',
	version='0.1',
	packages=['api'],
	package_dir = {'':'src'},
	entry_points={ \
		'telldus.plugins': [
			'api = api.ApiManager',
		]
	},
	extras_require = {
		'api': ['Telldus>=0.1\nWeb>=0.1'],
	},
	package_data={'api' : [
		'htdocs/*.js',
	]}
)
