import copy
import datetime
from typing import Any

from flask import flash

from flask_app.models import user, event
from flask_app.utils.data_cleaning import remove_excessive_newlines
from flask_app.utils.database import get_database


class EventComment:
    def __init__(self, data: dict):
        self.id = data['id']
        self.created_at = data['created_at']
        self.updated_at = data['updated_at']
        self.user_id = data['user_id']
        self.event_id = data['event_id']
        self.comment = data['comment']

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

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'user_id': self.user_id,
            'event_id': self.event_id,
            'comment': self.comment,
        }

    @staticmethod
    def clean_data(data: dict) -> dict:
        data = copy.deepcopy(data)

        if 'comment' in data:
            data['comment'] = remove_excessive_newlines(data['comment'])

        return data

    @classmethod
    def validate_new_comment(cls, data: dict) -> bool:
        is_valid = True

        # Check that all required fields exist.
        for key in ('user_id', 'event_id', 'comment'):
            if key not in data:
                flash("The value '{}' is missing.".format(key.replace('_', ' ')))
                is_valid = False
        if not is_valid:
            return is_valid

        if user.User.get_by_id(data['user_id']) is None:
            flash("The specified user cannot be found.")
            is_valid = False
        if event.Event.get_by_id(data['event_id']) is None:
            flash("The specified event cannot be found.")
            is_valid = False
        if len(data['comment']) < 5:
            flash("The provided comment was less than five characters long.")
            is_valid = False
        if len(data['comment']) > 500:
            flash("The provided comment was greater than five hundred characters long.")
            is_valid = False

        return is_valid

    @classmethod
    def create(cls, data: dict) -> int:
        # Manually set created_at and updated_at times to UTC so that
        # JavaScript can later convert to local time for the client.
        data = copy.deepcopy(data)
        data = cls.clean_data(data)
        data['created_at'] = datetime.datetime.utcnow()
        data['updated_at'] = datetime.datetime.utcnow()

        db = get_database()
        return db.execute_insert(
            """
            INSERT INTO event_comments (created_at, updated_at, user_id, event_id, comment)
            VALUES (
                %(created_at)s,
                %(updated_at)s,
                %(user_id)s,
                %(event_id)s,
                %(comment)s
            );
            """,
            data
        )

    @classmethod
    def get_by_id(cls, id: int, *args, **kwargs) -> Any or None:
        db = get_database()
        items = db.execute_query(
            """
            SELECT * FROM event_comments WHERE id = %(id)s LIMIT 1;
            """,
            {'id': id, }
        )
        if len(items) > 0:
            return cls(items[0])
        else:
            return None

    @classmethod
    def get_by_user_id(cls, user_id: int, *args, **kwargs) -> list:
        db = get_database()
        items = db.execute_query(
            """
            SELECT * FROM event_comments WHERE user_id = %(user_id)s;
            """,
            {'user_id': user_id, }
        )
        result = []
        for item in items:
            result.append(cls(item))
        return result

    @classmethod
    def get_by_event_id(cls, event_id: int, *args, **kwargs) -> list:
        db = get_database()
        items = db.execute_query(
            """
            SELECT * FROM event_comments WHERE event_id = %(event_id)s;
            """,
            {'event_id': event_id, }
        )
        result = []
        for item in items:
            result.append(cls(item))
        return result

    @classmethod
    def get_by_user_id_and_event_id(cls, user_id: int, event_id: int, *args, **kwargs) -> list:
        db = get_database()
        items = db.execute_query(
            """
            SELECT * FROM event_comments WHERE
                user_id = %()s AND
                event_id = %()s;
            """,
            {
                'user_id': user_id,
                'event_id': event_id,
            }
        )
        result = []
        for item in items:
            result.append(cls(item))
        return result

    def update(self):
        # Manually set time to UTC so that it can be converted to client's local time by JavaScript later.
        data = self.to_dict()
        data['updated_at'] = datetime.datetime.utcnow()

        db = get_database()
        db.execute_query(
            """
            UPDATE event_comments SET
                updated_at = %(updated_at)s,
                comment = %(comment)s
            WHERE
                id = %(id)s;
            """,
            data
        )

    @classmethod
    def delete_by_id(cls, id: int, *args, **kwargs):
        db = get_database()
        db.execute_query(
            """
            DELETE FROM event_comments WHERE id = %(id)s;
            """,
            {'id': id, }
        )
