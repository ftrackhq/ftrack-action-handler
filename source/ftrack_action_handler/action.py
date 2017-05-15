# :coding: utf-8
# :copyright: Copyright (c) 2017 ftrack

import logging

import ftrack_api

class BaseAction(object):
    '''Custom Action base class'''

    label = None
    identifier = None
    description = None

    def __init__(self, session):
        self.logger = logging.getLogger(
            '{0}.{1}'.format(__name__, self.__class__.__name__)
        )

        if self.label is None:
            raise ValueError(
                'Action missing label.'
            )

        elif self.identifier is None:
            raise ValueError(
                'Action missing identifier.'
            )

        self._session = session

    @classmethod
    def clone_session(cls, session):
        assert (
            isinstance(session, ftrack_api.Session)
        ), 'Must be ftrack_api.Session instance.'

        return ftrack_api.Session(
            session.server_url, session.api_key, session.api_user
        )

    def register(self):
        self._session.event_hub.subscribe(
            'topic=ftrack.action.discover', self._discover
        )

        self._session.event_hub.subscribe(
            'topic=ftrack.action.launch and data.actionIdentifier={0}'.format(
                self.identifier
            ),
            self._launch
        )

    def _discover(self, event):
        args = self._translate_event(
            self._session, event
        )

        accepts = self.discover(
            self._session, *args
        )

        if accepts:
            return {
                'items': [{
                    'label': self.label,
                    'description':self.description,
                    'actionIdentifier': self.identifier,
                }]
            }

    def discover(self, session, uid, entities, user, values):
        '''Return true if we can handle the selected entities.

        *session* is a `ftrack_api.Session` instance

        *uid* is the unique identifier for the event

         *entities* is a list of tuples each containing the
         entity type and the entity id.

         *values* is a dictionary containing potential user settings

        '''

        return False

    def _translate_event(self, session, event):
        '''Return *event* translated structure to be used with the API.'''

        _uid = event['source']['id']
        _user = event['source']['user']['id']

        _values = event['data'].get('values', {})
        _selection = event['data'].get('selection', [])

        _entities = list()
        for entity in _selection:
            _entities.append(
                (
                    self._get_entity_type(entity), entity.get('entityId')
                )
            )

        return [
            _uid,
            _entities,
            _user,
            _values
        ]

    def _get_entity_type(self, entity):
        '''Return translated entity type tht can be used with API.'''
        entity_type = entity.get('entityType')
        object_typeid = entity.get('objectTypeId')

        for schema in self._session.schemas:
            alias_for = schema.get('alias_for')

            if (
                alias_for and isinstance(alias_for, dict) and
                alias_for['id'].lower() == entity_type and
                object_typeid == alias_for.get('classifiers', {}).get('object_typeid')
            ):
                return schema['id']

        for schema in self._session.schemas:
            alias_for = schema.get('alias_for')

            if (
                alias_for and isinstance(alias_for, basestring) and
                alias_for.lower() == entity_type
            ):
                return schema['id']

        for schema in self._session.schemas:
            if schema['id'].lower() == entity_type:
                    return schema['id']

        raise ValueError(
            'Unable to translate entity type.'
        )

    def _launch(self, event):
        args = self._translate_event(
            self._session, event
        )

        interface = self._interface(
            self._session, *args
        )

        if interface:
            return interface

        response = self.launch(
            self._session, *args
        )

        return self._handle_result(
            self._session, response, *args
        )


    def launch(self, session, uid, entities, user, values):
        '''Callback method for the custom action

        *session* is a `ftrack_api.Session` instance

        *uid* is the unique identifier for the event

         *entities* is a list of tuples each containing the
         entity type and the entity id.

         *values* is a dictionary containing potential user settings
         from previous runs.

        '''
        raise NotImplementedError()

    def _interface(self, *args):
        interface = self.interface(*args)

        if interface:
            return {
                'items': interface
            }

    def interface(self, session, uid, entities, user, values):
        '''Return a interface if applicable or None

        *session* is a `ftrack_api.Session` instance

        *uid* is the unique identifier for the event

         *entities* is a list of tuples each containing the
         entity type and the entity id.

         *values* is a dictionary containing potential user settings
         from previous runs.

        '''

        return None

    def _handle_result(self, session, result, uid, entities, user, values):
        '''Validate the returned result from the action callback'''

        if not isinstance(result, dict):
            raise ValueError(
                'Launch must return a dictionary received : {0}.'.format(
                    type(result)
                )
            )

        for key in ('success', 'message'):
            if key in result:
                continue

            raise KeyError(
                'Missing required key : {0}.'.format(key)
            )

        session.commit()

        return result