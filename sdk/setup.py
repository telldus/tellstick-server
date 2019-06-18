# -*- coding: utf-8 -*-

from setuptools import setup

setup(
	name='sdk',
	version='0.1',
	packages=['sdk'],
	entry_points={
		'console_scripts': [
			'telldus = sdk.cli:main'
		],
		'distutils.commands': [
			'telldus_plugin = sdk.plugin:telldus_plugin'
		],
		'distutils.setup_keywords': [
			'category = sdk.plugin:telldus_plugin.validate_attribute',
			'color = sdk.plugin:telldus_plugin.validate_attribute',
			'compatible_platforms = sdk.plugin:telldus_plugin.validate_attribute',
			'icon = sdk.plugin:telldus_plugin.validate_attribute',
			'required_features = sdk.plugin:telldus_plugin.validate_attribute',
			'ports = sdk.plugin:telldus_plugin.validate_attribute',
		],
		'egg_info.writers': [
			'metadata.yml = sdk.plugin:telldus_plugin.write_metadata',
		],
	},
)
