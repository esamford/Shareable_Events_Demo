from typing import Any

from flask import flash

from flask_app.models import event
from flask_app.utils.database import get_database


class PrivateEvent:
    def __init__(self, data: dict):
        self.event_id = data['event_id']
        self.created_at = data['created_at']
        self.updated_at = data['updated_at']
        self.secret_key = data['secret_key']

        self.__event = None

    def get_event(self):
        if self.__event is None:
            self.__event = event.Event.get_by_id(self.event_id)
        return self.__event

    def to_dict(self) -> dict:
        return {
            'event_id': self.event_id,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'secret_key': self.secret_key,
        }

    @classmethod
    def validate_new_private_event(cls, data: dict, ignore_event_id_check: bool = False) -> bool:
        is_valid = True

        for key in ('secret_key', ):
            if key not in data:
                flash("The '{}' field was not provided.".format(key))
                is_valid = False
        if not is_valid:
            return is_valid

        if not ignore_event_id_check:
            if 'event_id' not in data:
                flash("The 'event_id' field was not provided.")
                is_valid = False
                return is_valid
            if event.Event.get_by_id(data['event_id']) is None:
                flash("The provided event ID cannot be found.")
                is_valid = False
        if len(data['secret_key']) < 5:
            flash("The provided secret key was less than five characters long.")
            is_valid = False
        if len(data['secret_key']) > 50:
            flash("The provided secret key was greater than fifty characters long.")
            is_valid = False

        return is_valid

    @classmethod
    def validate_access_with_event_id_and_secret_key(cls, event_id: int, secret_key: str, *args, **kwargs) -> bool:
        is_valid = True

        if event.Event.get_by_id(event_id) is None:
            is_valid = False
            return is_valid

        private_event = cls.get_by_event_id(event_id)
        if private_event is not None and private_event.secret_key != secret_key:
            is_valid = False

        return is_valid

    @classmethod
    def create(cls, data: dict):
        if event.Event.get_by_id(data['event_id']) is None:
            raise Exception("The event does not exist.")

        db = get_database()
        return db.execute_insert(
            """
            INSERT INTO private_events (event_id, secret_key)
            VALUES (
                %(event_id)s,
                %(secret_key)s
            );
            """,
            data
        )

    @classmethod
    def get_by_event_id(cls, event_id: int, *args, **kwargs) -> Any or None:
        db = get_database()
        items = db.execute_query(
            """
            SELECT * FROM private_events WHERE event_id = %(event_id)s LIMIT 1;
            """,
            {'event_id': event_id, }
        )
        if len(items) > 0:
            return cls(items[0])
        else:
            return None

    def update(self):
        db = get_database()
        db.execute_query(
            """
            UPDATE private_events SET
                secret_key = %(secret_key)s
            WHERE
                event_id = %(event_id)s;
            """,
            self.to_dict()
        )

    @classmethod
    def delete_by_event_id(cls, event_id: int, *args, **kwargs):
        db = get_database()
        db.execute_query(
            """
            DELETE FROM private_events WHERE event_id = %(event_id)s;
            """,
            {'event_id': event_id, }
        )


