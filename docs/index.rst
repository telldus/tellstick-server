.. TellStick ZNet documentation master file, created by
   sphinx-quickstart on Thu Dec 17 18:08:13 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to the TellStick developer documentation!
=================================================

TellStick ZNet allows developers to build own plugins and scripts run the device
to extend the functionality with features not yet supported by Telldus.

It is also possible to alter the behaviour on how TellStick ZNet should
interpret signals and messages from devices.

Intro
-----

TellStick ZNet offers two ways of integrating custom scripts. They can be
written in either Python or Lua. The difference is outlined below.

Python
######

Python plugins offers the most flexible solution since full access to the service is exposed.
This also makes it fragile since Python plugins can affect the service negative.

Lua
###

Lua code is available on both TellStick ZNet Pro and TellStick ZNet Lite. Lua
code runs in a sandbox and has only limited access to the system.

To create a Lua script you need to access the local web server in TellStick ZNet.
Browse to: http://[ipaddress]/lua to access the editor.

Lua codes works by signals from the server triggers the execution.

.. toctree::
   :hidden:
   :caption: Getting started
   :maxdepth: 1

   gettingstarted/installation

.. toctree::
   :hidden:
   :caption: Lua
   :maxdepth: 2

   lua/overview
   lua/api

.. toctree::
   :hidden:
   :caption: Python
   :maxdepth: 2

   python/intro
   python/concepts
   python/examples
   python/reference

.. toctree::
   :hidden:
   :caption: Local REST Api
   :maxdepth: 2

   api/intro
   api/authentication
   api/extending
