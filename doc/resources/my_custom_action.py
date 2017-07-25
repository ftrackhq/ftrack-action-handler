# :coding: utf-8
import logging

import ftrack_api

from ftrack_action_handler.action import BaseAction


class MyCustomAction(BaseAction):
    '''Custom action.'''

    #: A unique identifier for your action.
    identifier = 'my.custom.action'

    #: A descriptive string identifying your action to the user.
    label = 'My Action'

    #: Optionally set to differentiate actions with the same label
    variant = None

    #: A verbose descriptive text for you action
    description = 'This is an example action'

    def discover(self, session, entities, event):
        '''Return True if we can handle the discovery.'''
        # TODO: Modify to fit your needs.
        # Example, only allow a single asset version as selection.
        if len(entities) != 1:
            return

        entity_type, entity_id = entities[0]
        if entity_type != 'AssetVersion':
            return

        return True

    def launch(self, session, entities, event):
        '''Callback action'''
        for entity_type, entity_id in entities:
            entity = session.get(entity_type, entity_id)
            # TODO: Do something with the entity.
            return True


def register(session, **kw):
    '''Register plugin. Called when used as an plugin.'''
    # Validate that session is an instance of ftrack_api.Session. If not,
    # assume that register is being called from an old or incompatible API and
    # return without doing anything.
    if not isinstance(session, ftrack_api.session.Session):
        return

    action_handler = MyCustomAction(session)
    action_handler.register()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    session = ftrack_api.Session()
    register(session)

    # Wait for events
    logging.info('Registered actions and listening for events. Use Ctrl-C to abort.')
    session.event_hub.wait()
