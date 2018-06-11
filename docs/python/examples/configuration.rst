==========================
Configurations for plugins
==========================

If your plugin needs user set configuration values it can add this by using configurations.

Wrap your pluginclass with the :py:func:`@configuration <base.configuration>` decorator.

::

  from base import configuration, ConfigurationString, Plugin, ConfigurationList

  @configuration(
    companyName = ConfigurationString(
        defaultValue='Telldus Technologies',
        title='Company Name',
        description='Name of the Company'
    ),
    contacts = ConfigurationList(
        defaultValue=['9879879879', '8529513579', '2619859867'],
        title='company contacts',
        description='Contacts of the company',
        minLength=2
    ),
    username = ConfigurationString(
        defaultValue='admin@gmail.com',
        title='Username',
        description='Username of the company Administrator'
    ),
    password = ConfigurationString(
        defaultValue='admin1234',
        title='Password',
        description='Password of the company Administrator',
        minLength=8,
        maxLength=12
    )
  )
  class Config(Plugin):
    def companyInfo(self):
        # access the companyName information from the configuration
        return {
            'companyName' : self.config('companyName'),
            'contacts' : self.config('contacts'),
            'username' : self.config('username'),
            'password' : self.config('password'),
        }

Here, the configuration store company information and return it when it called.

The configuration has following classes:

:py:class:`base.ConfigurationString`: this function use to store configuration value as a string.

:py:class:`base.ConfigurationNumber`: this function use to store configuration value as a number.

:py:class:`base.ConfigurationList`: this function use to store configuration value as a list.

:py:class:`base.ConfigurationDict`: this function use to store configuration value as a dictionary.


Call configuration to get company information using lua script :

::

  local companyObject = require "configuration.Config"
  local companyData = companyObject:companyInfo()
