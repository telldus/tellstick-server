# -*- coding: utf-8 -*-

try:
	from setuptools import setup
except ImportError:
	from distutils.core import setup

setup(
	name='Base',
	version='0.1',
	packages=['base'],
	package_dir = {'':'src'},
	entry_points={ \
		'telldus.main': ['.rst = base:Application [cREQ]']
	},
	extras_require = dict(cREQ = 'Board>=0.1'),
)
