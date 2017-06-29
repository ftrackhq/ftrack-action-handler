..
    :copyright: Copyright (c) 2017 ftrack

.. _using:

*****
Using
*****

This package only contains one class `BaseAction`. It simplifies the configuration of a new
action by registering with the event hub and converting the events emitted from the server
to a more pythonic data representation.

The example actions below can be run directly or added to your ftrack connect plugin path
for more information see the main ftrack `documentation <http://ftrack-python-api.rtd.ftrack.com/en/latest/understanding_sessions.html#configuring-plugins>`_.

Example action
==============

This example registers a new action which only shows up when a single version
is selected in the ftrack interface.


.. literalinclude:: /resources/my_custom_action.py
    :language: python


Example action with interface
=============================

Display a interface asking the user for input in order to find and replace
words in a specified attribute name on the currently selected items.

.. literalinclude:: /resources/find_and_replace.py
    :language: python
