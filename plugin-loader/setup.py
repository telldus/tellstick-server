#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
	from setuptools import setup
	from setuptools.command.install import install
except ImportError:
	from distutils.core import setup
	from distutils.command.install import install
import os

class buildweb(install):
	def run(self):
		print("generate web application")
		os.system('npm install')
		os.system('npm run build')
		install.run(self)

setup(
	name='Plugin loader',
	version='0.1',
	packages=['pluginloader'],
	package_dir = {'':'src'},
	cmdclass={'install': buildweb},
	entry_points={ \
		'telldus.startup': ['c = pluginloader:Loader [cREQ]']
	},
	extras_require = dict(cREQ = 'Base>=0.1\nTelldusWeb>=0.1'),
	package_data={'pluginloader' : [
		'htdocs/plugins.js',
		'files/telldus.gpg',
	]}
)
