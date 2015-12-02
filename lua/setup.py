#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
	from setuptools import setup
except ImportError:
	from distutils.core import setup

setup(
	name='Lua',
	version='0.1',
	packages=['lua'],
	package_dir = {'':'src'},
	entry_points={ \
		'telldus.plugins': ['c = lua:Lua [cREQ]']
	},
	extras_require = dict(cREQ = 'Base>=0.1\nTelldus>=0.1\nTelldusWeb>=0.1'),
	package_data={'lua' : [
		'templates/*.html',
		'htdocs/*.js',
		'htdocs/*.css',
	]}
)
