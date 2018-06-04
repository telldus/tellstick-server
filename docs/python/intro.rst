
Python plugins
--------------

Python plugins offers the most flexible way of extending the functionality of TellStick. To get started a development environment should first be setup on a computer running Linux or macOS. Windows is not supported at the moment.


Plugins
*******

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

Plugin internals
################
.. toctree::

  anatomy
  deploy
