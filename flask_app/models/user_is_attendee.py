from typing import Any

from flask import flash

from flask_app.models import user, attendee
from flask_app.models.exception import SiteException
from flask_app.utils.database import get_database


class UserIsAttendee:
    def __init__(self, data: dict):
        self.user_id = data['user_id']
        self.attendee_id = data['attendee_id']
        self.created_at = data['created_at']
        self.updated_at = data['updated_at']

        self.__user = None
        self.__attendee = None
        self.__event = None

    def get_user(self):
        if self.__user is None:
            self.__user = user.User.get_by_id(self.user_id)
        return self.__user

    def get_attendee(self):
        if self.__attendee is None:
            self.__attendee = attendee.Attendee.get_by_id(self.attendee_id)
        return self.__attendee

    """def get_event(self):
        if self.__event is None:
            attendee_item = self.get_attendee()
            assert isinstance(attendee_item, attendee.Attendee)
            self.__event = event.Event.get_by_id(attendee_item.event_id)
        return self.__event"""

    @classmethod
    def validate_new_user_is_attendee(cls, data: dict) -> bool:
        is_valid = True

        # Check that all required fields exist.
        for key in ('user_id', 'attendee_id', ):
            if key not in data:
                flash("The value '{}' is missing.".format(key.replace('_', ' ')))
                is_valid = False
        if not is_valid:
            return is_valid

        if user.User.get_by_id(data['user_id']) is None:
            ex = Exception(
                "The user with the id = {} does not exist in the database. "
                "Cannot create new user_is_attendee record.".format(data['user_id'])
            )
            SiteException.create(type=str(type(ex)), message=str(ex))
            is_valid = False
        if attendee.Attendee.get_by_id(data['attendee_id']) is None:
            ex = Exception(
                "The attendee with the id = {} does not exist in the database. "
                "Cannot create new user_is_attendee record.".format(data['attendee_id'])
            )
            SiteException.create(type=str(type(ex)), message=str(ex))
            is_valid = False

        return is_valid

    @classmethod
    def create(cls, data: dict) -> None:
        db = get_database()
        db.execute_query(
            """
            INSERT INTO user_is_attendee (user_id, attendee_id)
            VALUES (
                %(user_id)s,
                %(attendee_id)s
            );
            """,
            data
        )

    @classmethod
    def get_by_user_id(cls, user_id: int, *args, **kwargs) -> list:
        db = get_database()
        items = db.execute_query(
            """
            SELECT * FROM user_is_attendee WHERE user_id = %(user_id)s;
            """,
            {'user_id': user_id, }
        )
        result = []
        for item in items:
            result.append(cls(item))
        return result

    @classmethod
    def get_by_attendee_id(cls, attendee_id: int, *args, **kwargs) -> Any or None:
        db = get_database()
        items = db.execute_query(
            """
            SELECT * FROM user_is_attendee WHERE attendee_id = %(attendee_id)s LIMIT 1;
            """,
            {'attendee_id': attendee_id, }
        )
        if len(items) > 0:
            return cls(items[0])
        else:
            return None

    @classmethod
    def delete_by_user_id_and_attendee_id(cls, user_id: int, attendee_id: int, *args, **kwargs):
        db = get_database()
        db.execute_query(
            """
            DELETE FROM user_is_attendee
            WHERE
                user_id = %(user_id)s AND
                attendee_id = %(attendee_id)s;
            """,
            {
                'user_id': user_id,
                'attendee_id': attendee_id,
            }
        )

    @classmethod
    def cascade_deleted_user_to_attendees(cls, user_id: int, *args, **kwargs):
        for uia_record in cls.get_by_user_id(user_id):
            attendee.Attendee.delete_by_id(uia_record.attendee_id)

    @classmethod
    def get_by_user_id_and_event_id(cls, user_id: int, event_id: int, *args, **kwargs) -> Any or None:
        db = get_database()
        items = db.execute_query(
            """
            SELECT user_is_attendee.*
            FROM
                users,
                user_is_attendee,
                attendees,
                events
            WHERE
                users.id = user_is_attendee.user_id AND
                user_is_attendee.attendee_id = attendees.id AND
                attendees.event_id = events.id AND
                users.id = %(user_id)s AND
                events.id = %(event_id)s
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



