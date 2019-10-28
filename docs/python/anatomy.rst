Anatomy of a plugin
###################

TellStick plugins are packaged as python eggs combined in a zip file. The eggs are signed with a pgp signature.

The metadata for a plugin is described in the file setup.py. This is a standard setuptools file with a couple custom configurations added.

.. code::

  #!/usr/bin/env python3
  # -*- coding: utf-8 -*-

  try:
  	from setuptools import setup
  except ImportError:
  	from distutils.core import setup

  setup(
  	name='Dummy device',
  	version='1.0',
  	author='Alice',
  	author_email='alice@wonderland.lit',
  	category='appliances',
  	color='#2c3e50',
  	description='Dummy template for implementings device plugins',
  	icon='dummy.png',
  	long_description="""
  		This plugin is used as a template when creating plugins that support new device types.
  	""",
  	packages=['dummy'],
  	package_dir = {'':'src'},
  	entry_points={ \
  		'telldus.startup': ['c = dummy:Dummy [cREQ]']
  	},
  	extras_require = dict(cREQ = 'Base>=0.1\nTelldus>=0.1'),
  )

Most of the fields can be found in the `setuptools documentation <http://setuptools.readthedocs.io/en/latest/setuptools.html>`_.

:author:
  The name of the developer of the plugin. This name must match the pgp signin certificate.
:author_email:
  The email of the developer of the plugin. This must match the pgp singning certificate.
:category:
  This must be one of:

  - security
  - weather
  - climate
  - energy
  - appliances
  - multimedia
  - notifications
:color:
  A color used in plugin selection user interface in the format #000000.
:compatible_platforms:
  Reserved for future use.
:description:
  A short description of the plugins. This should only be one line.
:entry_points:
  TellStick plugins can be loaded by one of two entry points.

  :telldus.startup:
    This plugin will auto load on startup. Use this when it is important that the plugin is always loaded.

  :telldus.plugins:
    This plugin will be loaded on-demand. This speeds up loading times and keep the memory footprint to a minimum.

:icon:
  Filename of icon in size 96x96.
:long_description:
  A long description describing the plugin. Markdown can be used.
:name:
  The name of the plugin.
:packages:
  A list of python packages included in the plugin. This should match the folder structure of the files.
  Please see setuptools documentation for more information.
:required_features:
  Reserved for future use.
:version:
  The version of the plugin.
