
Python plugins
--------------

Python plugins offers the most flexible way of extending the functionality of TellStick. To get started a development environment should first be setup on a computer running Linux or macOS. Windows is not supported at the moment.

Installation
############

Check out and follow the instructions on getting the server software running on a computer here:  
https://github.com/telldus/tellstick-server

Telldus own plugins are open source and can be used as a base for new plugins. These can be found here:  
https://github.com/telldus/tellstick-server-plugins

This guide will describe the example plugin found here:  
https://github.com/telldus/tellstick-server-plugins/tree/master/templates/device

The plugin adds one dummy device to the system.

During the development it is recommended to install it within the server software. This way the software will
restart itself whenever a file has changed. To install it use the tellstick command ``install``:

::

  ./tellstick.sh install [path-to-plugin]

Replace `[path-to-plugin]` with the path to the plugin root folder.

Anatomy of a plugin
###################

TellStick plugins are packaged as python eggs combined in a zip file. The eggs are signed with a pgp signature.

The metadata for a plugin is described in the file setup.py. This is a standard setuptools file with a couple custom configurations added.

.. code::

  #!/usr/bin/env python
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

Building a deployable plugin
############################

Once development is finished it's time to package the code into a deployable package. Before this command a working
pgp code signing key must be setup on the computer. The name and email must match the metadata ``author`` and ``author_email`` specified in setup.py.

Setting up a key
================

You can safely skip this step if you already have a pgp-key setup on your computer.

::

  gpg --gen-key

This will take you through a few questions that will configure your keys.

::

  Please select what kind of key you want: (1) RSA and RSA (default)
  What keysize do you want? 4096
  Key is valid for? 0
  Is this correct? y
  Real name: Enter the same name as in setup.py
  Email address: Enter the same email as in setup.py
  Comment:
  Change (N)ame, (C)omment, (E)mail or (O)kay/(Q)uit? O
  Enter passphrase: Enter a secure passphrase here (upper & lower case, digits, symbols)

Build the plugin
================

To build the package use the ``build-plugin`` command to tellstick.sh

::

  ./tellstick.sh build-plugin [path-to-plugin]

Replace `[path-to-plugin]` with the path to the plugin root folder. During building the plugin
will be signed using your pgp key and if a passphrase has been setup you will be asked for your password.

This will build a .zip file ready to be uploaded to a TellStick.
                                
