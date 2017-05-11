#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
	from setuptools import setup
except ImportError:
	from distutils.core import setup
import os

if 'HWBOARD' not in os.environ:
	print('HWBOARD environmental variable not set')
	quit(1)

setup(
	name='Board',
	version='0.1',
	packages=['board'],
	package_dir = {'':os.environ['HWBOARD']},
)
