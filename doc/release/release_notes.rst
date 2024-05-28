..
    :copyright: Copyright (c) 2014-2020 ftrack

.. _release/release_notes:

*************
Release Notes
*************

.. release:: Upcoming
    .. change:: changed
        :tags: API

        Provide run_as_user property in :ref:`AdvancedBaseAction <api_reference/AdvancedBaseAction>` to run the action as the user executing it.

    .. change:: changed
        :tags: Installer

        Allow to install for ftrack-python-api 3.0.

    .. change:: changed
        :tags: API

        Remove _get_entity_type from AdvancedBaseAction and rely on base class implementation.

.. release:: 0.3.0
    :date: 2022-05-11

    .. change:: changed
        :tags: API

        Refactor code to split baseclasses in separate modules.

    .. change:: new
        :tags: API

        Provide new :ref:`AdvancedBaseAction <api_reference/AdvancedBaseAction>` to allow more granular and complete control over the action behaviour.
        
        .. note::

            Contribution by `johannes.hezer <johannes.hezer@accenture.com>`_ .


.. release:: 0.2.1
    :date: 2020-05-05

    .. change:: fixed
        :tags: API

        Breaking import module.

.. release:: 0.2.0
    :date: 2020-04-28

    .. change:: new
        :tags: API

        Use setuptools_scm for versioning.

    .. change:: new
        :tags: API

        Add support for Python 3

.. release:: 0.1.4
    :date: 2019-10-31

    .. change:: new
        :tags: Action

        Add support for icons.

.. release:: 0.1.3
    :date: 2018-09-13

    .. change:: new
        :tags: API

        Add session property for easier access.

.. release:: 0.1.2
    :date: 2018-02-23

    .. change:: fixed
        :tags: Action

        Variants not handled correctly.

.. release:: 0.1.0
    :date: 2017-09-11

    .. change:: new
        :tags: Action, Event, API

        Base class for simplifying the creation of new actions and working with the new
        API.


