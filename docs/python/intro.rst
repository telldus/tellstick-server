
Python plugins
--------------

Python plugins offers the most flexible way of extending the functionality of TellStick. To get started a development environment should first be setup on a computer running Linux or macOS. Windows is not supported at the moment.

Installation Process
####################

TellStick server Installation
______________________________

This is the software running on the late generation TellStick ZNet Lite and
TellStick Net

Prerequisites
*************

This software is only supported under Linux and macOS.

Although most of the prerequisites can be installed sandboxed, locally in the
project folder, there are some libraries that must exist on the system.

* The following applications must be available:
	* python (2.7)
	* virtualenv
	* Node.js


Clone the Server code from here: https://github.com/telldus/tellstick-server


Linux
*****

In many Linux distributions the packages for `python` and `virtualenv` already exist.
On a Debian/Ubuntu based system these can be installed using this command:

::

  sudo apt-get install python virtualenv

If `virtualenv` is not available on your system, you can install it with either
`pip` or `easy install`:

::

  sudo pip install virtualenv

or

::

  sudo easy_install virtualenv

macOS
*****

Pyhon is already shipped on macOS. You only need to install `virtualenv` using:

::

  sudo easy_install virtualenv

Setup
*****

To setup the source and prepare the base plugins run the following script:

::

  ./tellstick.sh setup

This vill create a `virtualenv` folder under the `build` folder and download
and install the required libraries for running the software.
The installation is completely sandboxed and nothing is installed in the system.
You can wipe the `build` folder at any time to remove any installed packages.

Running
*******

Start the server by issuing:

:: 

  ./tellstick.sh run

By default the server will restart itself any time it detects a file has been
modified.



Plugins
*******

Check out and follow the instructions on getting the server software running on a computer here:
https://github.com/telldus/tellstick-server

After installation the tellstick server is installed without any plugins. For development the lua-plugin is a
recommended plugin to install. Install it with::

::

  ./tellstick.sh install lua

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