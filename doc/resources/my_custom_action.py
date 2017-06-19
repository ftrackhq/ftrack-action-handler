import logging

import ftrack_api

from ftrack_action_handler.action import (
    BaseAction
)


class MyCustomAction(BaseAction):
    '''Custom action.'''

    label = 'My Action'
    identifier = 'my.custom.action'
    description = 'This is an example action'

    def discover(self, session, uid, entities, source, values, event):
        '''Return True if we can handle the discovery.'''

        # Only acknowlage the discovery if the selection
        # contains a single asset version
        if len(entities) != 1:
            return

        entity_type, entity_id = entities[0]

        if entity_type != 'AssetVersion':
            return

        return True

    def launch(self, session, uid, entities, source, values, event):
        '''Callback action'''

        for entity_type, entity_id in entities:
            version = session.get(
                entity_type, entity_id
            )

            # DO SOMETHING WITH THE VERSION
            return True



def register(session, **kw):
    '''Register plugin. Called when used as an plugin.'''

    # Validate that session is an instance of ftrack_api.Session. If not,
    # assume that register is being called from an old or incompatible API and
    # return without doing anything.
    if not isinstance(session, ftrack_api.session.Session):
        return


    action_handler = MyCustomAction(
        session
    )

    action_handler.register()



if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO
    )

    session = ftrack_api.Session()

    register(session)

    # Wait for event for 100 seconds
    session.event_hub.wait(
        duration=100
    )

