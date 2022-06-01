import copy
import datetime
from typing import Any

from flask_app.models import client_ip_address
from flask_app.models.exception import SiteException
from flask_app.utils.database import get_database


class SecurityLog:
    def __init__(self, data: dict):
        self.id = data['id']
        self.created_at = data['created_at']
        self.updated_at = data['updated_at']
        self.client_ip_address_id = data['client_ip_address_id']
        self.log_type = data['log_type']

    @classmethod
    def validate_new_record(cls, data: dict) -> bool:
        is_valid = True

        # Check that all required fields exist.
        for key in ('client_ip_address_id', 'log_type'):
            if key not in data:
                ex = Exception(
                    "The '{}' field was not provided during the validation for an SecurityLog record."
                    .format(key)
                )
                SiteException.create(type=str(type(ex)), message=str(ex))
                is_valid = False
        if not is_valid:
            return is_valid

        if client_ip_address.ClientIPAddress.get_by_id(data['client_ip_address_id']) is None:
            ex = Exception(
                "The ClientIPAddress record with an ID of '{}' does not exist in the database. "
                "Cannot create a new SecurityLog record."
                .format(data['client_ip_address_id'])
            )
            SiteException.create(type=str(type(ex)), message=str(ex))
            is_valid = False
        if len(data['log_type']) < 2:
            ex = Exception(
                "The issue type is less than two characters long. "
                "Cannot create a new SecurityLog record."
                .format(data['log_type'])
            )
            SiteException.create(type=str(type(ex)), message=str(ex))
            is_valid = False

        return is_valid

    @classmethod
    def clean_data(cls, data: dict) -> dict:
        data = copy.deepcopy(data)

        if 'log_type' in data:
            data['log_type'] = str(data['log_type']).upper()

        return data

    @classmethod
    def create(cls, data: dict) -> int:
        db = get_database()
        return db.execute_insert(
            """
            INSERT INTO security_logs (client_ip_address_id, log_type)
            VALUES (
                %(client_ip_address_id)s,
                %(log_type)s
            );
            """,
            cls.clean_data(data)
        )

    @classmethod
    def get_by_id(cls, id: int) -> Any or None:
        db = get_database()
        items = db.execute_query(
            """
            SELECT * FROM security_logs WHERE id = %(id)s LIMIT 1;
            """,
            {'id': id, }
        )
        if len(items) > 0:
            return cls(items[0])
        else:
            return None

    @classmethod
    def get_by_client_ip_address_id(cls, client_ip_address_id: int, *args, **kwargs) -> list:
        db = get_database()
        items = db.execute_query(
            """
            SELECT * FROM security_logs
            WHERE
                client_ip_address_id = %(client_ip_address_id)s;
            """,
            {'client_ip_address_id': client_ip_address_id, }
        )
        result = []
        for item in items:
            result.append(cls(item))
        return result

    @classmethod
    def get_by_client_ip_address_id_and_log_type(cls, client_ip_address_id: int, log_type: str, *args, **kwargs):
        db = get_database()
        items = db.execute_query(
            """
            SELECT * FROM security_logs
            WHERE
                client_ip_address_id = %(client_ip_address_id)s AND
                log_type = %(log_type)s;
            """,
            cls.clean_data(
                {
                    'client_ip_address_id': client_ip_address_id,
                    'log_type': log_type,
                }
            )
        )
        result = []
        for item in items:
            result.append(cls(item))
        return result

    @classmethod
    def get_by_client_ip_address_id_and_log_type_after_created_at(
            cls, client_ip_address_id: int, log_type: str, created_at: datetime.datetime, *args, **kwargs
    ):
        db = get_database()
        items = db.execute_query(
            """
            SELECT * FROM security_logs
            WHERE
                client_ip_address_id = %(client_ip_address_id)s AND
                log_type = %(log_type)s AND
                created_at >= %(created_at)s;
            """,
            cls.clean_data(
                {
                    'client_ip_address_id': client_ip_address_id,
                    'log_type': log_type,
                    'created_at': created_at,
                }
            )
        )
        result = []
        for item in items:
            result.append(cls(item))
        return result

    @classmethod
    def get_by_log_type(cls, log_type: str, *args, **kwargs):
        db = get_database()
        items = db.execute_query(
            """
            SELECT * FROM security_logs
            WHERE
                log_type = %(log_type)s;
            """,
            cls.clean_data(
                {
                    'log_type': log_type,
                }
            )
        )
        result = []
        for item in items:
            result.append(cls(item))
        return result

    @classmethod
    def delete_by_id(cls, id: int):
        db = get_database()
        db.execute_query(
            """
            DELETE FROM security_logs WHERE id = %(id)s;
            """,
            {'id': id, }
        )
