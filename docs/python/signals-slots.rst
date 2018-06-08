=================
Signals and slots
=================

Signals and slots is another way of inter plugin communication. It is built on the
:doc:`observers framework <observers>` but offers a more loosley coupled integration. It's benefit
against observers is:

* The observers (slots) does not need to import the interface from the publishers (signal). This
  allows the plugin to be loaded even when the publishing plugin is not available.
* The slots can be named freely so name collision is not as likley to occur.

The drawbacks instead are:

* The publishers does not know anything about the observers so it's not possible the return a value
  from the observers. If a return value is required then use :doc:`observers <observers>` instead.

Signals
=======

To trigger an event or send some data to an observer a Signal is used. A signal is created by using
the decorator :py:func:`@signal <base.signal>`.

Example:

::

  from base import Plugin, signal

  class MyPlugin(Plugin):
    @signal('mysignal')
    def foobar(self):
      # Every time this function is called the signal "mysignal" is fired
      logging.warning("mysignal is fired")

    @signal
    def hello(self):
        # This signal takes the function name as the signal name
        logging.warning("signal hello is fired")


Slots
=====

To receive a signal a plugin declares a slot. The plugin must implement
:class:`base.ISignalObserver` to be able to receive any signals. Then use the decorator
:py:func:`@slot <base.slot>` on the function you wish to be called when the signal is fired.

Example:

::

  from base import implements, ISignalObserver, Plugin, slot

  class AnotherPlugin(Plugin):
    implements(ISignalObserver)

    @slot('mysignal')
    def foobar(self):
      logging.warning('Slot foobar was triggered by the signal "mysignal"')
