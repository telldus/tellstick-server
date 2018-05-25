
Extending
=========

It's possible to extend the API with new functions from :doc:`custom plugins </python/intro>`.

Prepare the plugin
##################

In order for the API plugin to know about this plugin it must implement the
interface ``IApiCallHandler``

.. code::

  from api import IApiCallHandler
  from base import Plugin, implements

  class HelloWorld(Plugin):
  	implements(IApiCallHandler)


Export a function
#################

Use the decorator ``@apicall`` on the function you want to export. This example
exports the function ``helloworld/foobar``:

.. code::

  @apicall('helloworld', 'foobar')
  def myfunction(self, arg1, arg2):


A complete example
##################

.. code::

  from api import IApiCallHandler, apicall
  from base import Plugin, implements

  class HelloWorld(Plugin):
  	implements(IApiCallHandler)

  	@apicall('helloworld', 'foobar')
  	def myfunction(self, arg1, arg2):
  		"""
  		Docs for the function goes here
  		"""
  		return True
