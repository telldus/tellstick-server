# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
	name='Base',
	version='0.1',
	packages=find_packages('src'),
	package_dir = {'':'src'},
	entry_points={ \
		'telldus.main': ['.rst = base:Application']
	},
	namespace_packages = ['base'],
)
