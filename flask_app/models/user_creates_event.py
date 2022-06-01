from typing import Any

from flask import flash

from flask_app.models import user, event
from flask_app.models.exception import SiteException
from flask_app.utils.database import get_database


class UserCreatesEvent:
    def __init__(self, data: dict):
        self.user_id = data['user_id']
        self.event_id = data['event_id']
        self.created_at = data['created_at']
        self.updated_at = data['updated_at']

        self.__user = None
        self.__event = None

    def get_user(self):
        if self.__user is None:
            self.__user = user.User.get_by_id(self.user_id)
        return self.__user

    def get_event(self):
        if self.__event is None:
            self.__event = event.Event.get_by_id(self.event_id)
        return self.__event

    @classmethod
    def validate_new_user_creates_event(cls, data: dict, ignore_missing_event: bool = False) -> bool:
        is_valid = True

        for key in ('user_id', ):
            if key not in data:
                flash("The '{}' field was not provided.".format(key))
                is_valid = False
        if not is_valid:
            return is_valid

        if user.User.get_by_id(data['user_id']) is None:
            ex = Exception(
                "The user with the id = {} does not exist in the database. "
                "Cannot create new user_creates_events record.".format(data['user_id'])
            )
            SiteException.create(type=str(type(ex)), message=str(ex))
            is_valid = False
        if not ignore_missing_event:
            if 'event_id' not in data:
                ex = Exception(
                    "The 'event_id' field was not provided during the validation for user_creates_event."
                )
                SiteException.create(type=str(type(ex)), message=str(ex))
                is_valid = False
                return is_valid
            if event.Event.get_by_id(data['event_id']) is None:
                ex = Exception(
                    "The event with the id = {} does not exist in the database. "
                    "Cannot create new user_creates_events record.".format(data['event_id'])
                )
                SiteException.create(type=str(type(ex)), message=str(ex))
                is_valid = False

        return is_valid

    @classmethod
    def create(cls, data: dict):
        db = get_database()
        return db.execute_insert(
            """
            INSERT INTO user_creates_event (user_id, event_id)
            VALUES (
                %(user_id)s, %(event_id)s
            );
            """,
            data
        )

    @classmethod
    def get_by_user_id(cls, user_id: int, *args, **kwargs) -> list:
        db = get_database()
        items = db.execute_query(
            """
            SELECT * FROM user_creates_event WHERE user_id = %(user_id)s;
            """,
            {'user_id': user_id, }
        )
        result = []
        for item in items:
            result.append(cls(item))
        return result

    @classmethod
    def get_by_event_id(cls, event_id: int, *args, **kwargs) -> Any or None:
        """
        Events may or may not have been created by one user per event, which is why no 'user_id' attribute
        is stored in the events table.
        """
        db = get_database()
        items = db.execute_query(
            """
            SELECT * FROM user_creates_event WHERE event_id = %(event_id)s LIMIT 1;
            """,
            {'event_id': event_id, }
        )
        if len(items) > 0:
            return cls(items[0])
        else:
            return None

    @classmethod
    def get_by_user_id_and_event_id(cls, user_id: int, event_id: int, *args, **kwargs) -> Any or None:
        db = get_database()
        items = db.execute_query(
            """
            SELECT * FROM user_creates_event WHERE
                user_id = %(user_id)s AND
                event_id = %(event_id)s
            LIMIT 1;
            """,
            {
                'user_id': user_id,
                'event_id': event_id,
            }
        )
        if len(items) > 0:
            return cls(items[0])
        else:
            return None

    @classmethod
    def delete_by_user_id_and_event_id(cls, user_id: int, event_id: int, *args, **kwargs):
        db = get_database()
        db.execute_query(
            """
            DELETE FROM user_creates_event
            WHERE
                user_id = %(user_id)s AND
                event_id = %(event_id)s;
            """,
            {
                'user_id': user_id,
                'event_id': event_id,
            }
        )