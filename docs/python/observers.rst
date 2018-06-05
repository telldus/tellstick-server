================
Observer pattern
================

Inter plugin communication is based on an observer pattern. Any plugin that wishes to publish events
or pull information from other plugins may register an interface to observe.

Both observers and publishers must inherit from the ``Plugin`` base class.

Publish the observer interface
==============================

An observer interface is a class that inherits ``IInterface`` and contains only static functions.
Example:

.. code::

  class IExampleObserver(IInterface):
  	"""Example observer interface exporting two functions"""
  	def foo():
  		"""Example function no 1"""
  	def bar():
  		"""Example function no 2"""


The class that uses this creates and observer collection.

.. code::

  class ExamplePlugin(Plugin):
  	observers = ObserverCollection(IExampleObserver)

Multiple plugins may observe the interface but only one plugin may create the observer collection.
Calling the observers can be made all by one och one by one by iterating the collection. The calling
the whole collection at once the returned value by each observer will be discarded. It the return
value is needed you must iterate and call each observer individually.

.. code::

  def callAllTheFoes(self):
  	self.observers.foo()  # Note, the returned value cannot be used

  def enterTheBars(self):
  	for observer in self.observers:
  		retVal = observer.bar()
  		if retVal is True:
  			logging.info("This bar is awesome")


Full example
------------

.. code::

  class IExampleObserver(IInterface):
  	"""Example observer interface exporting two functions"""
  	def foo():
  		"""Example function no 1"""
  	def bar():
  		"""Example function no 2"""

  class ExamplePlugin(Plugin):
  	observers = ObserverCollection(IExampleObserver)

Implementing the observer
=========================

To observe an interface the observing plugin must mask itself that it observes the interface by
using the ``implements()`` function.

.. code::

  class ExampleObserverPlugin(Plugin):
  	implements(IExampleObserver)


It can then implement the interface functions. Note that it's not necessary to implement all the
functions from the interface.

.. code::

  class ExamplePlugin(Plugin):
  	implements(IExampleObserver)

  	def bar(self):
  		return self.isThisBarAwseome
