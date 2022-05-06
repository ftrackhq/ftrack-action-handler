..
    :copyright: Copyright (c) 2017 ftrack

.. _release/migration:

***************
Migration notes
***************

No migration notes required at this time.


Upgrade to AdvancedBaseAction
=============================

With this release we introduce a new :ref:`AdvancedBaseAction <api_reference/AdvancedBaseAction>` to 
provide a more off the shelf set of functions to simplify the build of ftrack actions.


Being the new :ref:`AdvancedBaseAction <api_reference/AdvancedBaseAction>` class fully interchangeable with the :ref:`BaseAction <api_reference/BaseAction>`
    

Actions build on the :ref:`BaseAction <api_reference/BaseAction>` class can be easily 
upgraded to the new :ref:`AdvancedBaseAction <api_reference/AdvancedBaseAction>` changing the baseclass, from:

.. code::

    class MyActionClass(BaseAction):
        pass

to: 

.. code::

    class MyActionClass(AdvancedBaseAction):
        pass


The new baseclass can now start using the new features:

.. code::

    class MyActionClass(AdvancedBaseAction):
        limit_to_user = True


New methods and properties
--------------------------

Properties
^^^^^^^^^^

*  **allowed_roles** are the Roles allowed for this action to run.
*  **allowed_groups** are the  Groups allowed for this action to run.
*  **ignored_types** are the Types ignored for this action to run.
*  **allowed_types** are the Types allowed for this action to run.
*  **limit_to_user** is to Limit the action to the user which spans it.
*  **allow_empty_context** is to Allow to run without a selection.

Methods
^^^^^^^

*  **mark_job_as_failed** to mark the given job id as failed.
*  **mark_job_as_done** to mark the given job id as done.