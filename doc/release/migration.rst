..
    :copyright: Copyright (c) 2017 ftrack

.. _release/migration:

***************
Migration notes
***************

No migration notes required at this time.

Migrate to 0.3.0
================

With this release we introduce a new :ref:`AdvancedBaseAction <api_reference/AdvancedBaseAction>` to 
provide a more off the shelf set of functions to build ftrack actions.

.. note:: 
    
    The new  :ref:`AdvancedBaseAction <api_reference/AdvancedBaseAction>` class is fully interchangeable with the :ref:`BaseAction <api_reference/BaseAction>`

It provides new properties:

*  **allowed_roles** are the Roles allowed for this action to run.
*  **allowed_groups** are the  Groups allowed for this action to run.
*  **ignored_types** are the Types ignored for this action to run.
*  **allowed_types** are the Types allowed for this action to run.
*  **limit_to_user** is to Limit the action to the user which spans it.
*  **allow_empty_context** is to Allow to run without a selection.

And new methods:

*  **mark_job_as_failed** to mark the given job id as failed.
*  **mark_job_as_done** to mark the given job id as done.