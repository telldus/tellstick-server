#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
	from setuptools import setup
	from setuptools.command.install import install
except ImportError:
	from distutils.core import setup
	from distutils.command.install import install
import os

class webpack(install):
	def run(self):
		print("generate webpack application")
		os.system('npm install')
		os.system('npm run deploy')
		install.run(self)

setup(
	name='Telldus',
	version='0.1',
	packages=['telldus', 'telldus.web'],
	package_dir = {'':'src'},
	cmdclass={'install': webpack},
	entry_points={ \
		'telldus.plugins': [
			'api = telldus.DeviceApiManager',
			'react = telldus.web.React'
		]
	},
	extras_require = {
		'telldus': ['Base>=0.1\nEvent>=0.1'],
	},
	package_data={'telldus' : [
		'templates/*.html',
		'htdocs/img/*.png',
		'htdocs/img/*.ico',
		'htdocs/fonts/*.eot',
		'htdocs/fonts/*.tff',
		'htdocs/fonts/*.woff',
		'htdocs/fonts/*.woff2',
		'htdocs/js/*.js',
	]}
)
