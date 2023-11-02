import logging

from ftrack_action_handler import AdvancedBaseAction
import ftrack_api


class TestingAction(AdvancedBaseAction):
    run_as_user = True
    label = 'testing user action'
    identifier = 'com.ftrack.testing.user-action'

    def discover(self, session, entities, event):
        return True

    def launch(self, session, entities, event):
        print(session.api_user)


def register(api_object, **kw):
    '''Register hook with provided *api_object*.'''

    # Validate that session is an instance of ftrack_api.Session. If not,
    # assume that register is being called from an old or incompatible API and
    # return without doing anything.
    if not isinstance(api_object, ftrack_api.session.Session):
        return

    action = TestingAction(api_object)
    action.register()


if __name__ == '__main__':
    # To be run as standalone code.
    logging.basicConfig(level=logging.INFO)
    session = ftrack_api.Session(
        server_url='https://myserver.ftrackapp.com',
        api_user='oneuser',
        api_key='A-GLOBAL-API-KEY',
        auto_connect_event_hub=True
    )
    register(session)

    # Wait for events
    logging.info('Registered actions and listening for events. Use Ctrl-C to abort.')
    session.event_hub.wait()

