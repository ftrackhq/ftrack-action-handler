# :coding: utf-8
import logging

import ftrack_api

from ftrack_action_handler.action import AdvancedBaseAction


class ClearJobList(AdvancedBaseAction):
    identifier = "clear_joblist"
    label = "Clear Joblist"
    icon = "clear_joblist"
    action_description = "Removes all entries from the joblist of the triggering user"
    allowed_roles = []
    allowed_types = []
    allow_empty_context = True


    def launch(self, session, entities, event):

        user = self.get_action_user(event)
        success_message = {
            "success": True,
            "message": u"Joblist cleared"
        }
        error_message = {
            "success": False,
            "message": u"An error occured during job list clearing."
        }
        try:
            user_id = user["id"]
            job_query = self.session.query(
                u"select id, user, user_id"
                u" from Job where user_id = ‘{0}’".format(
                    user_id
                )
            ).all()
            for job in job_query:
                self.logger.debug(
                    u"Removing job: {0}".format(job)
                )
                self.session.delete(job)
            self.session.commit()

        except Exception as e:
            self.logger.error(str(e))
            return error_message

        return success_message

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    session = ftrack_api.Session()
    action = ClearJobList(session=session)
    action.register(standalone=True)

