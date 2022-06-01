from typing import Any

from flask import flash, session

from flask_app import BCRYPT_HASH_REGEX, bcrypt
from flask_app.models import event, user, user_is_attendee
from flask_app.utils.database import get_database
from flask_app.utils.passwords import bcrypt_password_if_not


class Attendee:
    def __init__(self, data: dict):
        self.id = data['id']
        self.created_at = data['created_at']
        self.updated_at = data['updated_at']
        self.event_id = data['event_id']
        self.first_name = data['first_name']
        self.last_name = data['last_name']
        self.password = data['password']

        self.__event = None
        self.__user = -1  # May be None, not User.

    def to_dict(self):
        return {
            'id': self.id,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'event_id': self.event_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'password': self.password,
        }

    def get_event(self):
        if self.__event is None:
            self.__event = event.Event.get_by_id(self.event_id)
        return self.__event

    def get_user_if_exists(self) -> Any or None:
        if self.__user == -1:
            uia = user_is_attendee.UserIsAttendee.get_by_attendee_id(self.id)
            if uia is None:
                self.__user = None
            else:
                assert isinstance(uia, user_is_attendee.UserIsAttendee)
                self.__user = user.User.get_by_id(uia.user_id)
        return self.__user

    @classmethod
    def validate_new_attendee(cls, data: dict, suppress_flash_messages: bool = False) -> bool:
        is_valid = True

        for key in ('event_id', 'first_name', 'last_name', 'password'):
            if key not in data:
                flash("The value '{}' is missing.".format(key.replace('_', ' ')))
                is_valid = False
        if suppress_flash_messages:
            session.pop('_flashes', None)
        if not is_valid:
            return is_valid

        if event.Event.get_by_id(data['event_id']) is None:
            flash("The provided event no longer exists.")
            is_valid = False
        if len(data['first_name']) < 2:
            flash("The provided first name was less than two characters long.")
            is_valid = False
        if len(data['first_name']) > 20:
            flash("The provided first name was greater than twenty characters long.")
            is_valid = False
        if len(data['last_name']) < 2:
            flash("The provided last name was less than two characters long.")
            is_valid = False
        if len(data['last_name']) > 20:
            flash("The provided last name was greater than twenty characters long.")
            is_valid = False

        # Passwords should be imported from the User object if the user is logged in. Don't check hashed passwords.
        if BCRYPT_HASH_REGEX.match(data['password']) is None:
            if len(data['password']) < 8:
                flash("The provided password was less than eight characters long.")
                is_valid = False
            if sum([bool(x in data['password']) for x in "!@#$%^&*()"]) == 0:
                flash("The provided password was missing one of the following special characters: ! @ # $ % ^ & * ( )")
                is_valid = False
            if sum([bool(x in data['password']) for x in "1234567890"]) == 0:
                flash("The provided password did not contain a number.")
                is_valid = False
            if str(data['password']) == str(data['password']).lower():
                flash("The provided password did not contain any capital letters.")
                is_valid = False
            if str(data['password']) == str(data['password']).upper():
                flash("The provided password did not contain any lowercase letters.")
                is_valid = False

        if suppress_flash_messages:
            session.pop('_flashes', None)

        return is_valid

    @classmethod
    def validate_attendee_login(cls, data: dict, suppress_flash_messages: bool = False) -> bool:
        is_valid = True

        for key in ('event_id', 'first_name', 'last_name', 'password'):
            if key not in data:
                flash("The value '{}' is missing.".format(key.replace('_', ' ')))
                is_valid = False
        if suppress_flash_messages:
            session.pop('_flashes', None)
        if not is_valid:
            return is_valid

        found_attendee = cls.get_by_all(**data)
        if found_attendee is None:
            if not suppress_flash_messages:
                flash("The name or password was incorrect.")
            is_valid = False
            return is_valid

        if suppress_flash_messages:
            session.pop('_flashes', None)
        return is_valid

    @classmethod
    def create(cls, data: dict) -> int:
        data['first_name'] = data['first_name'].title()
        data['last_name'] = data['last_name'].title()
        data['password'] = bcrypt_password_if_not(data['password'])

        db = get_database()
        return db.execute_insert(
            """
            INSERT INTO attendees (event_id, first_name, last_name, password)
            VALUES (
                %(event_id)s,
                %(first_name)s,
                %(last_name)s,
                %(password)s
            );
            """,
            data
        )

    @classmethod
    def create_from_user_id_and_event_id(cls, user_id: int, event_id: int, *args, **kwargs) -> int:
        found_user = user.User.get_by_id(user_id)
        if found_user is None:
            raise Exception(
                "The user with the id = {} does not exist in the database."
                "Cannot create new attendee based on user information.".format(user_id)
            )
        user_dict = found_user.to_dict()
        assert 'first_name' in user_dict
        assert 'last_name' in user_dict
        assert 'password' in user_dict
        user_dict['event_id'] = event_id

        if cls.validate_new_attendee(user_dict, suppress_flash_messages=True):
            return cls.create(user_dict)
        else:
            raise Exception("Could not create attendee from user_id and event_id.")

    @classmethod
    def get_by_id(cls, id: int, *args, **kwargs) -> Any or None:
        db = get_database()
        items = db.execute_query(
            """
            SELECT * FROM attendees WHERE id = %(id)s LIMIT 1;
            """,
            {'id': id, }
        )
        if len(items) > 0:
            return cls(items[0])
        else:
            return None

    @classmethod
    def get_by_user_id(cls, user_id: int, *args, **kwargs) -> list:
        user_is_attendee_list = user_is_attendee.UserIsAttendee.get_by_user_id(user_id)

        result = []
        for usa in user_is_attendee_list:
            assert isinstance(usa, user_is_attendee.UserIsAttendee)
            found_attendee = cls.get_by_id(usa.attendee_id)
            if found_attendee is not None:
                result.append(found_attendee)
        return result

    @classmethod
    def get_by_event_id(cls, event_id: int, *args, **kwargs) -> list:
        db = get_database()
        items = db.execute_query(
            """
            SELECT * FROM attendees WHERE event_id = %(event_id)s;
            """,
            {'event_id': event_id, }
        )
        result = []
        for item in items:
            result.append(cls(item))
        return result

    @classmethod
    def get_by_first_name(cls, first_name: str, *args, **kwargs) -> list:
        db = get_database()
        items = db.execute_query(
            """
            SELECT * FROM attendees WHERE first_name = %(first_name)s;
            """,
            {'first_name': first_name, }
        )
        result = []
        for item in items:
            result.append(cls(item))
        return result

    @classmethod
    def get_by_last_name(cls, last_name: str, *args, **kwargs) -> list:
        db = get_database()
        items = db.execute_query(
            """
            SELECT * FROM attendees WHERE last_name = %(last_name)s;
            """,
            {'last_name': last_name, }
        )
        result = []
        for item in items:
            result.append(cls(item))
        return result

    @classmethod
    def get_by_full_name(cls, first_name: str, last_name: str, *args, **kwargs) -> list:
        db = get_database()
        items = db.execute_query(
            """
            SELECT * FROM attendees WHERE
                first_name = %(first_name)s AND 
                last_name = %(last_name)s;
            """,
            {
                'first_name': first_name,
                'last_name': last_name,
            }
        )
        result = []
        for item in items:
            result.append(cls(item))
        return result

    @classmethod
    def get_by_full_name_and_event_id(
            cls, first_name: str, last_name: str, event_id: int, *args, **kwargs
    ) -> list:
        """
        NOTE: Multiple attendees for one event may have the same first and last names. Unregistered users
            may have a name, and registered users with the same name may appear as well.
        """
        db = get_database()
        items = db.execute_query(
            """
            SELECT * FROM attendees WHERE
                first_name = %(first_name)s AND 
                last_name = %(last_name)s AND
                event_id = %(event_id)s;
            """,
            {
                'first_name': first_name,
                'last_name': last_name,
                'event_id': event_id,
            }
        )
        result = []
        for item in items:
            result.append(cls(item))
        return result

    @classmethod
    def get_by_all(cls, event_id: int, first_name: str, last_name: str, password: str, *args, **kwargs) -> Any or None:
        attendees = cls.get_by_full_name_and_event_id(first_name=first_name, last_name=last_name, event_id=event_id)
        for attendee in attendees:
            if bcrypt.check_password_hash(attendee.password, password):
                return attendee
        return None

    @classmethod
    def get_record_count(cls) -> int:
        db = get_database()
        items = db.execute_query(
            """
            SELECT COUNT(id) AS 'count' FROM attendees;
            """
        )
        return items[0]['count']

    def update(self):
        data = self.to_dict()
        data['first_name'] = data['first_name'].title()
        data['last_name'] = data['last_name'].title()
        data['password'] = bcrypt_password_if_not(data['password'])

        db = get_database()
        db.execute_query(
            """
            UPDATE attendees SET
                event_id = %(event_id)s
                first_name = %(first_name)s,
                last_name = %(last_name)s,
                password = %(password)s
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
            DELETE FROM attendees WHERE id = %(id)s;
            """,
            {'id': id, }
        )

