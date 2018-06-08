
Module: base
==========================================

Classes in the base module are only accessible from Python applications.


.. autoclass:: base.Application
  :members:
  :exclude-members: registerScheduledTask

  .. automethod:: base.Application.registerScheduledTask(fn, seconds=0, minutes=0, hours=0, days=0, runAtOnce=False, strictInterval=False, args=None, kwargs=None)

.. autoclass:: base.mainthread
  :members:

.. autoclass:: base.ISignalObserver
  :show-inheritance:
  :members:

.. py:decorator:: base.signal

  This is a decorator for sending signals. Decorate any of your Plugins methods with this
  decorator and whenever the method is called the signal will be fired.

  Args:
    :name: The signal name. This can be omitted and then the function name will be used as the
      name of the signal.

.. py:decorator:: base.slot(message = '')

  This is a decorator for receiveing signals. The class must implement
  :class:`base.ISignalObserver`

  Args:
    :message: This is the signal name to receive
