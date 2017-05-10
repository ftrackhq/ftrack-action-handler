import Queue
import logging
import ftrack_api

from ftrack_action_handler.types import (
    FTRACK_JOB_STATUS
)

from ftrack_action_handler.utils.thread import (
    ActionWorker
)

class BaseAction(object):
    LABEL = None
    IDENTIFIER = None
    DESCRIPTION = None

    def __init__(self, session):
        self.logger = logging.getLogger(
            '{0}.{1}'.format(__name__, self.__class__.__name__)
        )

        if self.LABEL is None:
            raise ValueError(
                'action missing label!'
            )

        elif self.IDENTIFIER is None:
            raise ValueError(
                'action missing identifier!'
            )

        self._session = session

    @classmethod
    def clone_session(cls, session):
        assert (
            isinstance(session, ftrack_api.Session)
        ), 'Must be ftrack_api.Session instance'

        return ftrack_api.Session(
            session.server_url, session.api_key, session.api_user
        )

    def register(self):
        self._session.event_hub.subscribe(
            'topic=ftrack.action.discover', self._discover
        )

        self._session.event_hub.subscribe(
            'topic=ftrack.action.launch and data.actionIdentifier={0}'.format(
                self.IDENTIFIER
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
                    'label': self.LABEL,
                    'description':self.DESCRIPTION,
                    'actionIdentifier': self.IDENTIFIER,
                }]
            }

    def discover(self, session, uid, entities, user, values):
        '''Return true if we can handle the selected entities.

        `entities`is a list of tuples each containing the entity_type and id
        for the selected entities, `user` contains the id of the user requesting
        the descovery.
        '''

        return True

    def _translate_event(self, session, event):
        '''Translate the event to a suitable structure to be used
        with the API.'''

        _uid = event['source']['id']
        _user = event['source']['user']['id']

        _values = event['data'].get('values', {})
        _selection = event['data'].get('selection', [])

        return [
            _uid,
            [
                (self._get_entity_type(e), e.get('entityId')) for e in _selection
            ],
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

        raise ValueError('Unable to translate entity type.')

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
        raise NotImplementedError()

    def _interface(self, *args):
        interface = self.interface(*args)

        if interface:
            return {
                'items': interface
            }

    def interface(self, session, uid, entities, user, values):
        return None

    def _handle_result(self, session, result, uid, entities, user, values):
        if not isinstance(result, dict):
            raise ValueError(
                'launch must return a dictionary received : {0}'.format(
                    type(result)
                )
            )

        for key in ('success', 'message'):
            if key in result:
                continue

            raise KeyError(
                'missing required key : {0}'.format(key)
            )

        session.commit()

        return result


    def wait(self, duration=None):
        self._session.event_hub.wait(
            duration=duration
        )


class ResultBaseAction(BaseAction):
    LOCATION_ID = ftrack_api.symbol.SERVER_LOCATION_ID

    def __init__(self, session, threads=5):
        super(ResultBaseAction, self).__init__(
            session
        )

        self.queue = Queue.Queue()

        self.workers = [
            ActionWorker(self.queue) for i in range(threads)
        ]

    @classmethod
    def _create_job(cls, session, user_id):
        assert (
            isinstance(session, ftrack_api.Session)
        ), 'Must be ftrack_api.Session instance'

        return session.create('Job', {
            'user_id': user_id,
            'status': FTRACK_JOB_STATUS.RUNNING
        })

    def _launch(self, event):
        event_session = self.clone_session(
            self._session
        )
        uid, entities, user, values = self._translate_event(
            event_session, event
        )

        interface = self._interface(
            self._session, uid, entities, user, values
        )

        if interface:
            return interface

        job = self._create_job(
            event_session, user
        )

        event_session.commit()

        task = dict(
            fn = self.launch,
            args = (uid, entities, user, values, job),
            session = event_session,
            callback = self._handle_result
        )

        self.queue.put(task)


    def launch(self, session, uid, entities, user, values, job):
        raise NotImplementedError()

    def _handle_result(self, session, result, uid, entities, user, values, job):
        r = super(ResultBaseAction, self)._handle_result(
            session, result, uid, entities, user, values
        )

        path = result.get('path', None)

        if path:
            component = session.create_component(
                path, location=session.get('Location', self.LOCATION_ID)
            )

            session.create('JobComponent', {
                'job_id': job.get('id'),
                'component_id': component.get('id'),

            })

        job.update({
            'status':FTRACK_JOB_STATUS.DONE if \
                result['success'] else FTRACK_JOB_STATUS.FAILED
        })

        session.commit()

        return r


class SimpleAction(BaseAction):
    LABEL = 'simple action'
    IDENTIFIER = 'ftrack.test.simple_action'

    def discover(self, uid, session, entities, user, values):

        return True

    def launch(self, uid, session, entities, user, values):
        return {
            'success':False,
            'message':'sweet'
        }


    def interface(self, session, uid, entities, user, values):
        if values:
            return

        return [
            {
                'label': '',
                'type': 'enumerator',
                'name': 'type_id',
                'value':'two',
                'data': [
                    {'label':'one', 'value':'one'},
                    {'label':'two', 'value':'two'}]
            }
        ]




class CalculateAction(ResultBaseAction):
    LABEL = 'calculate action'
    IDENTIFIER = 'ftrack.test.calculcate_action'

    def discover(self, session, uid, entities, user, values):
        for entity_type, entity_id in entities:
            if entity_type.lower() == 'assetversion':
                return True

    def launch(self, session, uid, entities, user, values, job):
        import tempfile

        with tempfile.NamedTemporaryFile(delete=False) as f:
            for entity_type, entity_id in entities:
                f.write(
                    '{0}\n'.format(
                        session.get(entity_type, entity_id).get('id')
                    )
                )

        return {
            'success':False,
            'message':'sweet so confusd',
            'path':f.name,
        }

    def interface(self, session, uid, entities, user, values):
        if values:
            return

        return [
            {
                'label': '',
                'type': 'enumerator',
                'name': 'type_id',
                'value':'two',
                'data': [
                    {'label':'one', 'value':'one'},
                    {'label':'two', 'value':'two'}]
            }
        ]

"""
if __name__ == '__main__':

    session = ftrack_api.Session(
        api_key='4b5c2d64-2fdb-11e7-af7f-f23c91e05852', api_user='eric.hermelin@ftrack.com', server_url='https://ftrack.ftrackapp.com'
    )



    logging.basicConfig()

    for cls in (CalculateAction, SimpleAction):
        t = cls(session)

        t.register()

    t.wait()

    print "done"
    pass
"""
