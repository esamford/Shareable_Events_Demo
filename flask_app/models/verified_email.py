import datetime
import secrets
from typing import Any

import validators.email
from flask import flash, render_template

from flask_app import get_domain_address
from flask_app.models import user
from flask_app.models.exception import SiteException
from flask_app.utils.database import get_database
from flask_app.utils.email_utils import send_email


class VerifiedEmail:
    def __init__(self, data: dict):
        self.user_id = data['user_id']
        self.created_at = data['created_at']
        self.updated_at = data['updated_at']
        self.new_email = data['new_email']
        self.email_sent = data['email_sent']
        self.verified = data['verified']
        self.verification_code = data['verification_code']

        self.__user = None

    def to_dict(self) -> dict:
        return {
            'user_id': self.user_id,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'new_email': self.new_email,
            'email_sent': self.email_sent,
            'verified': self.verified,
            'verification_code': self.verification_code,
        }

    def get_user(self):
        if self.__user is None:
            self.__user = user.User.get_by_id(self.user_id)
        return self.__user

    @classmethod
    def validate_new_record(cls, data: dict) -> bool:
        is_valid = True

        # Check that all required fields exist.
        for key in ('user_id', 'new_email', 'email_sent', 'verified'):
            if key not in data:
                flash("The value '{}' is missing.".format(key.replace('_', ' ')))
                is_valid = False
        if not is_valid:
            return is_valid

        if user.User.get_by_id(data['user_id']) is None:
            ex = Exception(
                "The user with the ID number of {} does not exist in the database. "
                "Cannot validate a new VerifiedEmail record.".format(data['user_id'])
            )
            SiteException.create(type=str(type(ex)), message=str(ex))
            is_valid = False
        if not validators.email(data['new_email']):
            flash("The provided email address is invalid.")
            is_valid = False
        if data['email_sent'] not in (True, False, "1", "0", 1, 0):
            ex = Exception(
                "The 'email_sent' boolean was not as an expected value: {}".format(data['email_sent'])
            )
            SiteException.create(type=str(type(ex)), message=str(ex))
            is_valid = False
        if data['verified'] not in (True, False, "1", "0", 1, 0):
            ex = Exception(
                "The 'verified' boolean was not as an expected value: {}".format(data['verified'])
            )
            SiteException.create(type=str(type(ex)), message=str(ex))
            is_valid = False

        return is_valid

    @classmethod
    def validate_email_change(cls, data: dict) -> bool:
        is_valid = True

        # Check that all required fields exist.
        for key in ('user_id', 'new_email'):
            if key not in data:
                flash("The value '{}' is missing.".format(key.replace('_', ' ')))
                is_valid = False
        if not is_valid:
            return is_valid

        found_user = user.User.get_by_id(data['user_id'])
        found_email = user.User.get_by_email(data['new_email'])
        if found_user is None:
            flash("Could not find user.")
            is_valid = False
        if not validators.email(data['new_email']):
            flash("The provided email address is invalid.")
            is_valid = False
        if found_email.id != found_user.id:
            flash("Someone else is already using that email address.")
            is_valid = False
        if data['new_email'].lower() == found_user.email.lower():
            flash("You are already using that email address.")
            is_valid = False

        return is_valid

    @classmethod
    def create(cls, data: dict):
        if 'verification_code' not in data:
            data['verification_code'] = cls.generate_verification_code()

        db = get_database()
        db.execute_insert(
            """
            INSERT INTO verified_emails (user_id, new_email, email_sent, verified, verification_code)
            VALUES (
                %(user_id)s,
                %(new_email)s,
                %(email_sent)s,
                %(verified)s,
                %(verification_code)s
            );
            """,
            data
        )

    @classmethod
    def get_by_user_id(cls, user_id: int, *args, **kwargs) -> Any or None:
        db = get_database()
        items = db.execute_query(
            """
            SELECT * FROM verified_emails WHERE user_id = %(user_id)s LIMIT 1;
            """,
            {'user_id': user_id, }
        )
        if len(items) > 0:
            return cls(items[0])
        else:
            return None

    @classmethod
    def get_unverified_records(cls) -> list:
        db = get_database()
        items = db.execute_query(
            """
            SELECT * FROM verified_emails WHERE verified = %(verified)s;
            """,
            {'verified': False, }
        )
        result = []
        for item in items:
            result.append(cls(item))
        return result

    @classmethod
    def get_expired_records(cls) -> list:
        db = get_database()
        items = db.execute_query(
            """
            SELECT * FROM verified_emails
            WHERE
                verified = %(verified)s AND
                created_at = updated_at AND             -- Only get records that have never been verified.
                created_at <= %(max_creation_date)s;    -- Get records that are too old.
            """,
            {
                'verified': False,
                'max_creation_date': datetime.datetime.now() - datetime.timedelta(days=7)
            }
        )
        result = []
        for item in items:
            result.append(cls(item))
        return result

    def update(self):
        db = get_database()
        db.execute_query(
            """
            UPDATE verified_emails SET
                new_email = %(new_email)s,
                email_sent = %(email_sent)s,
                verification_code = %(verification_code)s,
                verified = %(verified)s
            WHERE
                user_id = %(user_id)s;
            """,
            self.to_dict()
        )

    # No delete by ID method. Records from this table should only be deleted when their associated user is deleted.

    @classmethod
    def delete_expired_users(cls):
        for record in cls.get_expired_records():
            user.User.delete_by_id(record.user_id)

    @staticmethod
    def generate_verification_code() -> str:
        return secrets.token_urlsafe(128)

    @classmethod
    def send_verification_email_to_address(cls, user_id: int, new_email: str):
        found_user = user.User.get_by_id(user_id)
        if found_user is None:
            raise Exception(
                "No user with the ID of {} was found in the database. Cannot send verification email.".format(user_id)
            )

        # Create a new record or modify an existing one so that it shows the email has not yet been sent.
        found_verification = cls.get_by_user_id(found_user.id)
        if found_verification is None:
            new_data = {
                'user_id': found_user.id,
                'new_email': new_email,
                'email_sent': False,
                'verified': False
            }
            if not cls.validate_new_record(new_data):
                ex = Exception("Could not validate new record for VerifiedEmail: {}".format(new_data))
                SiteException.create(type=str(type(ex)), message=str(ex))
                raise ex
            cls.create(new_data)
            found_verification = cls.get_by_user_id(found_user.id)
            assert found_verification is not None
        else:
            found_verification.verification_code = cls.generate_verification_code()
            found_verification.new_email = new_email
            found_verification.email_sent = False
            found_verification.verified = False
            found_verification.update()

        # Send the verification email.
        context = {
            'first_name': found_user.first_name,
            'verification_url': "{}/verify_email/{}/{}/".format(
                get_domain_address().strip('/'), found_user.id, found_verification.verification_code
            ),
            'domain': get_domain_address(),
        }
        rendered_template = render_template('/email_html/registration_email.html', **context)
        send_email(
            recipient_address=found_verification.new_email,
            subject="Verify Email",
            rendered_template=rendered_template
        )

        # Update the verified_emails record so that it shows the email was sent.
        found_verification.email_sent = True
        found_verification.update()

    @classmethod
    def send_verification_to_changed_email(cls, user_id: int, new_email: str):
        found_user = user.User.get_by_id(user_id)
        if found_user is None:
            raise Exception(
                "No user with the ID of {} was found in the database. Cannot send verification email.".format(user_id)
            )

        found_verification = cls.get_by_user_id(found_user.id)
        found_verification.new_email = new_email
        found_verification.email_sent = False
        found_verification.verified = False
        found_verification.update()

        # Send the verification email.
        verification_url = "{}/verify_email/{}/{}/".format(
            get_domain_address().strip('/'), found_user.id, found_verification.verification_code
        )
        body_text = "Hello, {}!\n\n" \
                    "We just received a request to change your email. " \
                    "If this was you, click the link below to validate your new address. " \
                    "If this was not you, please ignore this message and change your password.\n\n" \
                    "{}".format(
                        found_user.first_name, verification_url
                    )
        send_email(recipient_address=found_verification.new_email, subject="Verify Email Change", body=body_text)

        # Update the verified_emails record so that it shows the email was sent.
        found_verification.email_sent = True
        found_verification.update()


