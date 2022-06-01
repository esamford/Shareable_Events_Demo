from flask_app.utils.database import get_database


class SiteException:
    def __init__(self, data: dict):
        self.id = data['id']
        self.created_at = data['created_at']
        self.updated_at = data['updated_at']
        self.type = data['type']
        self.message = data['message']

    @classmethod
    def get_all(cls) -> list:
        db = get_database()
        items = db.execute_query(
            "SELECT * FROM exceptions;"
        )
        result = []
        for item in items:
            result.append(cls(item))
        return result

    @classmethod
    def get_by_id(cls, id: int, *args, **kwargs):
        db = get_database()
        items = db.execute_query(
            "SELECT * FROM exceptions WHERE id = %(id)s LIMIT 1;",
            {'id': id, }
        )
        if len(items) > 0:
            return cls(items[0])
        else:
            return None

    @classmethod
    def create(cls, type: str, message: str, *args, **kwargs) -> int:
        db = get_database()
        return db.execute_insert(
            """
            INSERT INTO exceptions (type, message)
            VALUES (
                %(type)s,
                %(message)s
            );
            """,
            {
                'type': type,
                'message': message,
            }
        )

    @classmethod
    def create_by_exception(cls, ex: Exception) -> int:
        return cls.create(type=str(type(ex)), message=str(ex))
