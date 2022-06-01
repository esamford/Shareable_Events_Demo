import datetime
from hashlib import sha256
from typing import Any

from flask_app.utils.database import get_database


class ClientIPAddress:
    def __init__(self, data: dict):
        self.id = data['id']
        self.created_at = data['created_at']
        self.updated_at = data['updated_at']
        self.ip_hash = data['ip_hash']

    def __str__(self):
        result = "{} ({}): ".format(self.id, self.created_at).ljust(30)
        result += "{}".format(self.ip_hash)
        return result

    @classmethod
    def validate_new_client_ip(cls, data: dict):
        is_valid = True

        for key in ('ip_address', ):
            if key not in data:
                is_valid = False
        if not is_valid:
            return is_valid

        if cls.get_by_ip_address(**data) is not None:
            is_valid = False

        return is_valid

    @staticmethod
    def get_hashed_ip(ip_address: str, *args, **kwargs) -> str:
        # Use SHA256 instead of Bcrypt because Bcrypt generates unique hashes that cannot be matched in MySQL.
        if ip_address.startswith('$'):
            return ip_address
        else:
            return '$' + sha256(ip_address.encode('utf-8')).hexdigest()

    @classmethod
    def create(cls, ip_address: str, *args, **kwargs) -> int:
        db = get_database()
        return db.execute_insert(
            """
            INSERT INTO client_ip_addresses (ip_hash)
            VALUES (
                %(ip_hash)s
            );
            """,
            {'ip_hash': cls.get_hashed_ip(ip_address), }
        )

    @classmethod
    def get_by_id(cls, id: int) -> Any or None:
        db = get_database()
        items = db.execute_query(
            """
            SELECT * FROM client_ip_addresses WHERE id = %(id)s LIMIT 1;
            """,
            {'id': id, }
        )
        if len(items) > 0:
            return cls(items[0])
        else:
            return None

    @classmethod
    def get_by_ip_address(cls, ip_address: str, *args, **kwargs) -> Any or None:
        db = get_database()
        items = db.execute_query(
            """
            SELECT * FROM client_ip_addresses WHERE ip_hash = %(ip_hash)s LIMIT 1;
            """,
            {
                'ip_hash': cls.get_hashed_ip(ip_address),
            }
        )
        if len(items) > 0:
            return cls(items[0])
        else:
            return None

    @classmethod
    def get_by_max_created_at(cls, created_at: datetime.datetime) -> list:
        db = get_database()
        items = db.execute_query(
            """
            SELECT * FROM client_ip_addresses WHERE created_at = %(created_at)s;
            """,
            {'created_at': created_at, }
        )
        result = []
        for item in items:
            result.append(cls(item))
        return result









