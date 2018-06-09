
Configuration for plugin
########################

Configuration plugin is the way where we define static data that used several times and anywhere in the project.

First, create `setup.py <http://tellstick-server.readthedocs.io/en/latest/python/anatomy.html>`_ file.

Create a plugin file and import ``configuration`` package from ``base`` to create configuration.

::

  from base import configuration, ConfigurationString, Plugin, ConfigurationList, ConfigurationManager

  __name__ = 'configuration'

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

    def getCompanyInfo(self):
        return {
            'companyName' : self.config('companyName'),
            'contacts' : self.config('contacts'),
            'username' : self.config('username'),
            'password' : self.config('password'),
        }

    def setCompanyInfo(self, companyName, contacts, username, password):
        self.setValue('companyName', companyName)
        self.setValue('contacts', contacts)
        self.setValue('username', username)
        self.setValue('password', password)


Here, ``getCompanyInfo`` function is used to get the information of the company from the configuration.

And the ``setCompanyInfo`` function is used to set the configuration value of the company.


The configuration has following classes:

``ConfigurationString`` : this function use to store configuration value as a string.

``ConfigurationNumber`` : this function use to store configuration value as a number.

``ConfigurationList`` : this function use to store configuration value as a list.

``ConfigurationDict`` : this function use to store configuration value as a dictionary.


Call configuration to get company information using lua script : 

::

  local companyObject = require "configuration.Config"
  local companyData = companyObject:companyInfo()
