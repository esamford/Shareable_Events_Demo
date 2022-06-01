import copy
import secrets
from typing import Any

from flask import flash, render_template

from flask_app import get_domain_address
from flask_app.models import user
from flask_app.models.exception import SiteException
from flask_app.utils.database import get_database
from flask_app.utils.email_utils import send_email


class PasswordReset:
    def __init__(self, data: dict):
        self.id = data['id']
        self.created_at = data['created_at']
        self.updated_at = data['updated_at']
        self.user_id = data['user_id']
        self.reset_code = data['reset_code']
        self.success = data['success']

        self.__user = None

    def get_user(self):
        if self.__user is None:
            self.__user = user.User.get_by_id(self.user_id)
        return self.__user

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'user_id': self.user_id,
            'reset_code': self.reset_code,
            'success': self.success
        }

    @classmethod
    def validate_new_record(cls, data: dict) -> bool:
        is_valid = True

        # Check that all required fields exist.
        for key in ('user_id', ):
            if key not in data:
                ex = Exception(
                    "The '{}' key is missing. Cannot validate new password reset record.".format(key)
                )
                SiteException.create_by_exception(ex)
                is_valid = False
        if not is_valid:
            return is_valid

        found_user = user.User.get_by_id(data['user_id'])
        if found_user is None:
            ex = Exception(
                "The user with an ID number of '{}' could not be found in the database. Cannot validate a new "
                "password reset record.".format(data['user_id'])
            )
            SiteException.create_by_exception(ex)
            is_valid = False
            return is_valid

        found_verified_email = found_user.get_email_verification()
        if not found_verified_email.verified:
            flash("The provided email address was never verified. We cannot send a password reset email.")
            is_valid = False

        return is_valid

    @classmethod
    def validate_show_reset_password_form(cls, data: dict) -> bool:
        is_valid = True

        # Check that all required fields exist.
        for key in ('user_id', 'reset_code'):
            if key not in data:
                ex = Exception(
                    "The '{}' key is missing. Cannot validate rendering of the password reset form.".format(key)
                )
                SiteException.create_by_exception(ex)
                is_valid = False
        if not is_valid:
            return is_valid

        found_password_reset = cls.get_most_recent_by_user_id(data['user_id'])
        if found_password_reset is None:
            is_valid = False
        elif found_password_reset.success:
            # Don't allow reset records to be used more than once.
            is_valid = False
        elif found_password_reset.reset_code != data['reset_code']:
            is_valid = False

        return is_valid

    @classmethod
    def validate_password_reset(cls, data: dict) -> bool:
        is_valid = True

        # Check that all required fields exist.
        for key in ('user_id', 'reset_code', 'password', 'confirm_password'):
            if key not in data:
                ex = Exception(
                    "The '{}' key is missing. Cannot validate rendering of the password reset form.".format(key)
                )
                SiteException.create_by_exception(ex)
                is_valid = False
        if not is_valid:
            return is_valid

        found_password_reset = cls.get_by_user_id_and_reset_code(**data)
        if found_password_reset is None:
            is_valid = False
        elif found_password_reset.success:
            # Don't allow reset records to be used more than once.
            is_valid = False
        elif found_password_reset.reset_code != data['reset_code']:
            is_valid = False

        if not user.User.validate_password(**data):
            is_valid = False

        return is_valid

    @classmethod
    def create(cls, data: dict) -> int:
        data = copy.deepcopy(data)
        data['reset_code'] = cls.generate_reset_code()
        data['success'] = False

        db = get_database()
        return db.execute_insert(
            """
            INSERT INTO password_resets (user_id, reset_code, success)
            VALUES (
                %(user_id)s,
                %(reset_code)s,
                %(success)s
            );
            """,
            data
        )

    @classmethod
    def get_by_id(cls, id: int, *args, **kwargs) -> Any or None:
        db = get_database()
        items = db.execute_query(
            """
            SELECT * FROM password_resets WHERE id = %(id)s LIMIT 1;
            """,
            {'id': id}
        )
        if len(items) > 0:
            return cls(items[0])
        else:
            return None

    @classmethod
    def get_most_recent_by_user_id(cls, user_id: int, *args, **kwargs) -> Any or None:
        db = get_database()
        items = db.execute_query(
            """
            SELECT * FROM password_resets
            WHERE
                user_id = %(user_id)s
            ORDER BY
                -created_at     /* Move the maximum datetime to the front. */
            LIMIT 1;
            """,
            {'user_id': user_id, }
        )
        if len(items) > 0:
            return cls(items[0])
        else:
            return None

    @classmethod
    def get_by_user_id_and_reset_code(cls, user_id: int, reset_code: str, *args, **kwargs) -> Any or None:
        db = get_database()
        items = db.execute_query(
            """
            SELECT * FROM password_resets
            WHERE
                user_id = %(user_id)s AND
                reset_code = %(reset_code)s
            ORDER BY
                -created_at     /* Move the maximum datetime to the front. */
            LIMIT 1;
            """,
            {'user_id': user_id, 'reset_code': reset_code}
        )
        if len(items) > 0:
            return cls(items[0])
        else:
            return None

    def update(self):
        db = get_database()
        db.execute_query(
            """
            UPDATE password_resets SET
                success = %(success)s
            WHERE
                id = %(id)s;
            """,
            self.to_dict()
        )

    @staticmethod
    def generate_reset_code() -> str:
        return secrets.token_urlsafe(128)

    @classmethod
    def send_password_reset_email_to_user(cls, user_id: int) -> (bool, int or None):
        """
        :param user_id: The ID number for the user who should receive a password reset email.
        :return: The first value indicates whether or not the email had been sent. The second is the ID number
            for the new password reset record.
        """
        new_data = {
            'user_id': user_id,
        }
        if not cls.validate_new_record(new_data):
            ex = Exception(
                "Could not validate a password reset record for the user with the ID of '{}'.".format(user_id)
            )
            SiteException.create_by_exception(ex)
            return False, None

        found_user = user.User.get_by_id(user_id)
        password_reset_obj = cls.get_by_id(cls.create(new_data))
        context = {
            'first_name': found_user.first_name,
            'password_reset_url': "{}/reset_password/{}/{}/".format(
                get_domain_address().strip('/'), found_user.id, password_reset_obj.reset_code),
            'domain': get_domain_address(),
        }

        try:
            rendered_template = render_template('/email_html/password_reset_email.html', **context)
            send_email(
                recipient_address=found_user.email,
                subject="Reset Your Password",
                rendered_template=rendered_template
            )
        except Exception:
            return False, password_reset_obj.id

        return True, password_reset_obj.id








