
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

.. automethod:: base.SignalManager.slot
