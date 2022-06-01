import copy
from typing import Any

import validators
from flask import flash

from flask_app import bcrypt
from flask_app.models import event, user_is_attendee, verified_email
from flask_app.utils.database import get_database
from flask_app.utils.passwords import bcrypt_password_if_not


class User:
    def __init__(self, data: dict):
        self.id = data['id']
        self.created_at = data['created_at']
        self.updated_at = data['updated_at']
        self.first_name = data['first_name']
        self.last_name = data['last_name']
        self.email = data['email']
        self.password = data['password']

        self.__created_events = None
        self.__attending_events = None
        self.__email_verification = None

    def __str__(self) -> str:
        result = "{} ({}): ".format(self.id, self.created_at).ljust(30)
        result += "{} {} ".format(self.first_name, self.last_name).ljust(30)
        result += " | {}".format(self.email)
        return result

    def to_dict(self):
        return {
            'id': self.id,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'password': self.password,
        }

    def get_created_events(self) -> list:
        if self.__created_events is None:
            self.__created_events = event.Event.get_by_author_id(self.id)
        return self.__created_events

    def get_attending_events(self) -> list:
        if self.__attending_events is None:
            self.__attending_events = event.Event.get_by_user_id_through_attendee(self.id)
        return self.__attending_events

    def get_email_verification(self) -> Any:
        if self.__email_verification is None:
            self.__email_verification = verified_email.VerifiedEmail.get_by_user_id(self.id)
        return self.__email_verification

    def is_attending_event_with_id(self, event_id: int) -> bool:
        if user_is_attendee.UserIsAttendee.get_by_user_id_and_event_id(self.id, event_id) is not None:
            return True
        else:
            return False

    @classmethod
    def clean_data(cls, data: dict) -> dict:
        data = copy.deepcopy(data)

        if 'first_name' in data:
            data['first_name'] = data['first_name'].strip(' ')
            data['first_name'] = data['first_name'].title()

        if 'last_name' in data:
            data['last_name'] = data['last_name'].strip(' ')
            data['last_name'] = data['last_name'].title()

        if 'email' in data:
            data['email'] = data['email'].lower()

        return data

    @staticmethod
    def validate_password(password: str, confirm_password: str, *args, **kwargs) -> bool:
        is_valid = True

        if len(password) < 8:
            flash("The provided password was less than eight characters long.")
            is_valid = False
        if sum([bool(x in password) for x in "!@#$%^&*()"]) == 0:
            flash("The provided password was missing one of the following special characters: ! @ # $ % ^ & * ( )")
            is_valid = False
        if sum([bool(x in password) for x in "1234567890"]) == 0:
            flash("The provided password did not contain a number.")
            is_valid = False
        if str(password) == str(password).lower():
            flash("The provided password did not contain any capital letters.")
            is_valid = False
        if str(password) == str(password).upper():
            flash("The provided password did not contain any lowercase letters.")
            is_valid = False
        if password != confirm_password:
            flash("The provided password did not match the confirmed password.")
            is_valid = False

        return is_valid

    @classmethod
    def validate_new_user(cls, data: dict) -> bool:
        is_valid = True

        data = cls.clean_data(data)

        # Check that all required fields exist.
        for key in ('first_name', 'last_name', 'email', 'password', 'confirm_password'):
            if key not in data:
                flash("The value '{}' is missing.".format(key.replace('_', ' ')))
                is_valid = False
        if not is_valid:
            return is_valid

        # Validate provided information.
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
        if not validators.email(data['email']):
            flash("The provided email address was not written as a valid email address.")
            is_valid = False
        if len(data['email']) < 10:
            flash("The provided email address was less than ten characters long.")
            is_valid = False
        if cls.get_by_email(data['email']) is not None:
            flash("The provided email address is already being used. If this is yours, please try logging in instead.")
            is_valid = False

        if not cls.validate_password(password=data['password'], confirm_password=data['confirm_password']):
            is_valid = False

        return is_valid

    @classmethod
    def validate_login(cls, data: dict):
        is_valid = True

        # Check that all required fields exist.
        for key in ('email', 'password'):
            if key not in data:
                flash("The '{}' field was not provided.".format(key))
                is_valid = False
        if not is_valid:
            return is_valid

        if len(data['email']) == 0:
            flash("No email address was provided.")
            is_valid = False
        if len(data['password']) == 0:
            flash("No password was provided.")
            is_valid = False
        if not is_valid:
            return is_valid

        # Check if a user with the provided email and password combination exists.
        user = cls.get_by_email_and_password(**data)
        if user is None:
            flash("The email and/or password was incorrect.")
            is_valid = False

        return is_valid

    @classmethod
    def validate_password_change(cls, data: dict) -> bool:
        is_valid = True

        # Check that all required fields exist.
        for key in ('user_id', 'current_password', 'new_password', 'confirm_password'):
            if key not in data:
                flash("The '{}' field was not provided.".format(key))
                is_valid = False
        if not is_valid:
            return is_valid

        found_user = cls.get_by_id(data['user_id'])
        if found_user is None:
            raise Exception(
                "The user with the ID = {} was not found in the "
                "database while validating password changes.".format(data['user_id'])
            )

        if not bcrypt.check_password_hash(found_user.password, data['current_password']):
            flash("The current password is not correct.")
            is_valid = False
        if not cls.validate_password(password=data['new_password'], confirm_password=data['confirm_password']):
            is_valid = False

        return is_valid

    @classmethod
    def create(cls, data: dict) -> int:
        data = cls.clean_data(data)
        data['password'] = bcrypt_password_if_not(data['password'])

        db = get_database()
        user_id = db.execute_insert(
            """
            INSERT INTO users (first_name, last_name, email, password)
            VALUES (
                %(first_name)s,
                %(last_name)s,
                %(email)s,
                %(password)s
            );
            """,
            data
        )

        # Verify new email address.
        try:
            verified_email.VerifiedEmail.send_verification_email_to_address(user_id=user_id, new_email=data['email'])
        except Exception as ex:
            cls.delete_by_id(user_id)
            raise ex

        return user_id

    @classmethod
    def get_by_id(cls, id: int, *args, **kwargs) -> Any or None:
        db = get_database()
        items = db.execute_query(
            """
            SELECT * FROM users WHERE id = %(id)s LIMIT 1;
            """,
            {'id': id}
        )
        if len(items) > 0:
            return cls(items[0])
        else:
            return None

    @classmethod
    def get_by_email(cls, email: str, *args, **kwargs) -> Any or None:
        db = get_database()
        items = db.execute_query(
            """
            SELECT * FROM users WHERE email = %(email)s LIMIT 1;
            """,
            {'email': email, }
        )
        if len(items) > 0:
            return cls(items[0])
        else:
            return None

    @classmethod
    def get_by_email_and_password(cls, email: str, password: str, *args, **kwargs) -> Any or None:
        user = cls.get_by_email(email)

        # If the user doesn't exist, return None.
        if user is None:
            return None

        # If the user exists, check that the password is correct. If not, return None.
        if bcrypt.check_password_hash(user.password, password):
            return user
        else:
            return None

    @classmethod
    def get_by_first_name(cls, first_name: str, *args, **kwargs) -> list:
        db = get_database()
        items = db.execute_query(
            """
            SELECT * FROM users WHERE first_name = %(first_name)s;
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
            SELECT * FROM users WHERE last_name = %(last_name)s;
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
            SELECT * FROM users WHERE
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
    def get_record_count(cls) -> int:
        db = get_database()
        items = db.execute_query(
            """
            SELECT COUNT(id) AS 'count' FROM users;
            """
        )
        return items[0]['count']

    def update(self):
        data = self.to_dict()
        data = self.clean_data(data)
        data['password'] = bcrypt_password_if_not(data['password'])

        db = get_database()
        db.execute_query(
            """
            UPDATE users SET
                first_name = %(first_name)s,
                last_name = %(last_name)s,
                email = %(email)s,
                password = %(password)s
            WHERE
                id = %(id)s;
            """,
            data
        )

    @classmethod
    def delete_by_id(cls, id: int, *args, **kwargs):
        # Delete all attendee records associated with this user. Everything else should be deleted automatically.
        user_is_attendee.UserIsAttendee.cascade_deleted_user_to_attendees(id)

        db = get_database()
        db.execute_query(
            """
            DELETE FROM users WHERE id = %(id)s;
            """,
            {'id': id, }
        )
