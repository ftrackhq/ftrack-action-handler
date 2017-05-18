..
    :copyright: Copyright (c) 2017 ftrack

.. _using:

*****
Using
*****

This package only contains one class `BaseAction`. It simplifies the configuration of a new
action by registring with the event hub and converting the events emitted from the server
to a more pythonic data representation.

Example action
==============

This example registers a new action which only shows up when a single version
is selected in the ftrack interface.


.. literalinclude:: /resources/my_custom_action.py
    :language: python

