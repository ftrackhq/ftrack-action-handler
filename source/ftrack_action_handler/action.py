# :coding: utf-8
# :copyright: Copyright (c) 2021 Mackevision

import json
import logging
import os
import uuid

logging.basicConfig(level=logging.INFO)
# --------------------------------------------------------------
# Base Action Class.
# --------------------------------------------------------------


class BaseAction(object):
    """Custom Action base class

    `label` a descriptive string identifying your action.

    `variant` To group actions together, give them the same
    label and specify a unique variant per action.

    `identifier` a unique identifier for your action.

    `description` a verbose descriptive text for you action

    """

    # Action fields
    label = None  # Required field
    variant = None
    identifier = None  # Required field
    description = None
    icon = None

    __KNOWN_TYPES__ = ["Context", "AssetVersion", "FileComponent"]

    # TODO: maybe always append uuid to identifier?

    # Action filters
    allowed_roles = []  # Roles allowed for this action to run
    allowed_groups = []  # Groups allowed for this action to run
    ignored_types = []  # Types ignored for this action to run
    allowed_types = []  # Types allowed for this action to run
    limit_to_user = None  # Limit the action to the user which spans it
    allow_empty_context = False  # Allow to run without a selection

    def __repr__(self):
        """Action object representation."""
        return "<{0}:{1}>".format(self.__class__.__name__, self.identifier)

    def __init__(self, session, limit_to_user=None, make_unique=False):
        """Expects a ftrack_api.Session instance and optional user limiter"""

        self.logger = logging.getLogger(
            "{0}.{1}".format(__name__, self.__class__.__name__)
        )
        # self.logger.setLevel(logging.DEBUG)

        if not all([self.label, self.identifier]):
            msg = (
                "Error initializing action {0} :"
                " mandatory variables are set to : {1}".format(
                    self.__class__.__name__,
                    ", ".join(
                        [
                            self.label or "No Action label Set",
                            self.identifier or "No Action identifier Set",
                        ]
                    ),
                )
            )

            self.logger.critical(msg)
            raise RuntimeError(msg)

        if limit_to_user:
            self.limit_to_user = limit_to_user
            # if the action is tied to one user only
            # we need to make the action name
            # unique otherwise it will
            # trigger all actions that are on the event hub
            # with that name
            self.identifier = "{}_{}".format(
                self.identifier, str(uuid.uuid4())
            )

        if not limit_to_user and make_unique:
            self.identifier = "{}_{}".format(
                self.identifier, str(uuid.uuid4())
            )

        self._session = session
        self.job_id = None

        prefix = os.getenv("FTRACK_ACTION_PREFIX", None)
        if prefix:
            self.label = "{} {}".format(prefix.title(), self.label)
            self.identifier = "{}_{}".format(prefix, self.identifier)

        self.logger.debug(self.label)
        self.logger.debug(self.identifier)

    # --------------------------------------------------------------
    # Default Action Properties
    # --------------------------------------------------------------
    @property
    def session(self):
        """Return current session."""
        return self._session

    # --------------------------------------------------------------
    # Custom Action methods
    # --------------------------------------------------------------

    def _identify_entity_(self, entity):
        """Identify provided *entity*."""

        entity_types = self.__KNOWN_TYPES__
        entity_type = None
        _id = entity.get("entityId")
        for entity_type in entity_types:
            entity = self.session.get(entity_type, _id)
            has_type = getattr(entity, "entity_type", None)
            if has_type:
                entity_type = has_type
                break

        if not entity_type:
            msg = "Could not identify entity {0}".format(entity)
            self.logger.critical(msg)
            raise RuntimeError(msg)

        return entity_type

    def _get_selection_(self, event):
        """From a raw *event* dictionary, extract the selected entities."""

        data = event["data"]
        selection = data.get("selection", [])
        return selection

    def get_action_user(self, event):
        """From a raw *event* dictionary, extract the source user, and
        return it in form of an :py:class:`ftrack.UserEntity`
        """

        return self.session.query(
            "select id, user_security_roles, username, memberships"
            ' from User where username is "{0}"'.format(
                event["source"]["user"]["username"]
            )
        ).one()

    def _check_permissions_(self, ftrack_user):
        """Checks that the specified *ftrack_user* has the permissions set in
        :py:attr:`base._base_action.BaseAction.ALLOWED_GROUPS` and
        :py:attr:`base._base_action.BaseAction.ALLOWED_ROLES`."""

        group_valid = True
        role_valid = True

        if not self.allowed_roles and not self.allowed_groups:
            return True

        if self.allowed_groups:
            group_valid = False
            groups = self.session.query(
                "select name, memberships from Group"
            ).all()

            group_users = []
            for group in groups:
                if group["name"] not in self.allowed_groups:
                    continue

                for member in group["memberships"]:
                    group_users.append(member)

            group_users = [x["username"] for x in group_users]
            if ftrack_user["username"] not in group_users:
                group_valid = False

        if self.allowed_roles:
            role_valid = False
            _roles = []
            roles = [
                r["security_role"]["name"]
                for r in ftrack_user["user_security_roles"]
            ]

            for role in roles:
                _roles.append(role in self.allowed_roles)
            role_valid = any(_roles)

        result = group_valid and role_valid
        return result

    def _check_allowed_types_(self, selection):
        """Check whether the entities in *selection* are among
        the :py:attr:`base._base_action.BaseAction.IGNORED_TYPES` or
        in :py:attr:`base._base_action.BaseAction.ALLOWED_TYPES`.
        """

        if not selection:
            if self.allow_empty_context:
                return True

            return False

        if self.ignored_types:
            for selected_item in selection:
                entity_type = self._identify_entity_(selected_item)
                if entity_type in self.ignored_types:
                    self.logger.debug(
                        "Ignoring. Item of type %s is in ignored types: %s",
                        entity_type,
                        self.ignored_types,
                    )
                    return False

        if self.allowed_types:
            for selected_item in selection:
                entity_type = self._identify_entity_(selected_item)
                if entity_type not in self.allowed_types:
                    self.logger.debug(
                        "Ignoring. Type %s it is not in allowed types: %s",
                        entity_type,
                        self.allowed_types,
                    )
                    return False

        return True

    def _check_limit_to_user_(self, action_user):
        """Check whether this action should be
        allowed only on the current user.
        """
        if self.limit_to_user is not None:
            if action_user["username"] != self.limit_to_user:
                return False
            return True
        return True

    def _translate_event(self, event):
        """Return *event* translated structure to be used with the API."""

        _selection = event["data"].get("selection", [])

        _entities = list()
        for entity in _selection:
            _entities.append(
                (self._get_entity_type(entity), entity.get("entityId"))
            )

        return _entities

    def _get_entity_type(self, entity):
        """Return translated entity type that can be used with API."""
        # Get entity type and make sure it is lower cased. Most places except
        # the component tab in the Sidebar will use lower case notation.
        entity_type = entity.get("entityType").replace("_", "").lower()

        for schema in self.session.schemas:
            alias_for = schema.get("alias_for")

            if (
                    alias_for
                    and isinstance(alias_for, str)
                    and alias_for.lower() == entity_type
            ):
                return schema["id"]

        for schema in self.session.schemas:
            if schema["id"].lower() == entity_type:
                return schema["id"]

        raise ValueError(
            "Unable to translate entity type: {0}.".format(entity_type)
        )

    # --------------------------------------------------------------
    # Default Action Methods
    # --------------------------------------------------------------

    def register(self, standalone=False):
        """Registers the action, subscribing the discover and launch topics."""
        self.session.event_hub.subscribe(
            "topic=ftrack.action.discover", self._discover
        )

        self.session.event_hub.subscribe(
            "topic=ftrack.action.launch and data.actionIdentifier={0}".format(
                self.identifier
            ),
            self._launch,
        )

        if standalone:
            self.logger.debug(
                'Action: {0} running as standalone.'.format(
                    self.label
                )
            )
            self.session.event_hub.wait()


    def _discover(self, event):
        entities = self._translate_event(event)
        self.logger.info(entities)
        discoverable = True

        # Check user.
        action_user = self.get_action_user(event)
        user_only = self._check_limit_to_user_(action_user)
        if not user_only:
            self.logger.debug(
                "Action %s is not enabled for user %s",
                self.identifier,
                action_user["username"],
            )

            discoverable = False

        # Collect and check selected entities.
        selection = self._get_selection_(event)
        is_allowed = self._check_allowed_types_(selection)
        if not is_allowed:
            self.logger.debug(
                "Action %s is not allowed for the selected types.",
                self.identifier,
            )
            discoverable = False

        # Check permissions and groups
        has_permissions = self._check_permissions_(action_user)
        if not has_permissions:
            self.logger.debug(
                "Action %s is not enabled user %s"
                " does not have permissions.",
                self.identifier,
                action_user["username"],
            )

            discoverable = False

        accepts = self.discover(self.session, entities, event)

        if accepts and discoverable:
            self.logger.debug("Action: %s discovered", self.label)
            return {
                "items": [
                    {
                        "icon": self.icon,
                        "label": self.label,
                        "variant": self.variant,
                        "description": self.description,
                        "actionIdentifier": self.identifier,
                    }
                ]
            }

    def discover(self, session, entities, event):
        """Return true if we can handle the selected entities.

        *session* is a `ftrack_api.Session` instance


        *entities* is a list of tuples each containing the entity type and the
        entity id. If the entity is a hierarchical you will always get the
        entity type TypedContext, once retrieved through a get operation you
        will have the "real" entity type ie. example Shot, Sequence
        or Asset Build.

        *event* the unmodified original event

        """

        return True

    def _launch(self, event):
        entities = self._translate_event(event)

        interface = self._interface(self.session, entities, event)

        if interface:
            return interface

        response = self.launch(self.session, entities, event)

        return self._handle_result(response)

    def launch(self, session, entities, event):
        """Callback method for the custom action.

        return either a bool (True if successful or False if the action failed)
        or a dictionary with they keys `message` and `success`, the message
        should be a string and will be displayed as feedback to the user,
        success should be a bool, True if successful or False if the action
        failed.

        *session* is a `ftrack_api.Session` instance

        *entities* is a list of tuples each containing the entity type and the
        entity id. If the entity is a hierarchical you will always get the
        entity type TypedContext, once retrieved through a get operation you
        will have the "real" entity type ie. example Shot, Sequence
        or Asset Build.

        *event* the unmodified original event

        """
        raise NotImplementedError()

    def _interface(self, session, entities, event):
        interface = self.interface(session, entities, event)

        if interface:
            return interface

    def interface(self, session, entities, event):
        """Return a interface if applicable or None

        *session* is a `ftrack_api.Session` instance

        *entities* is a list of tuples each containing the entity type and the
        entity id. If the entity is a hierarchical you will always get the
        entity type TypedContext, once retrieved through a get operation you
        will have the "real" entity type ie. example Shot, Sequence
        or Asset Build.

        *event* the unmodified original event
        """
        return None

    def _handle_result(self, result):
        """Validate the returned result from the action callback"""
        if isinstance(result, bool):
            result = {
                "success": result,
                "message": ("{0} launched successfully.".format(self.label)),
            }

        elif isinstance(result, dict):
            for key in ("success", "message"):
                if key in result:
                    continue

                raise KeyError("Missing required key: {0}.".format(key))

        else:
            self.logger.error(
                "Invalid result type must be bool or dictionary!"
            )

        return result

    # --------------------------------------------------------------
    # Job management.
    # --------------------------------------------------------------

    def create_job(self, event, description):
        """Create a new job."""
        user_id = event["source"]["user"]["id"]
        job = self.session.create(
            "Job",
            {
                "user": self.session.get("User", user_id),
                "status": "running",
                "data": json.dumps({"description": u"{}".format(description)}),
            },
        )
        self.session.commit()
        job_id = job.get("id")
        self.job_id = job_id
        return self.job_id

    def attach_component_to_job(self, job_id, component_id, description):
        """Attach a component to a job."""
        self.session.create(
            "JobComponent", {"component_id": component_id, "job_id": job_id}
        )

        job = self.session.get("Job", job_id)
        job["data"] = json.dumps({"description": u"{}".format(description)})
        job["status"] = "done"
        self.session.commit()

    def mark_job_as_failed(self, job_id, error_message):
        """Mark a job as failed."""

        job = self.session.get("Job", job_id)
        job["data"] = json.dumps({"description": u"{}".format(error_message)})
        job["status"] = "failed"
        self.session.commit()

    def mark_job_as_done(self, job_id, description):
        """Mark a job as done."""

        job = self.session.get("Job", job_id)
        job["data"] = json.dumps({"description": u"{}".format(description)})
        job["status"] = "done"
        self.session.commit()
