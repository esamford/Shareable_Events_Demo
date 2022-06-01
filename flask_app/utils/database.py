from flask_app import get_db_connection_settings
from flask_app.config.sqldatabase import SQLDatabase


def get_database() -> SQLDatabase:
    connection_settings = get_db_connection_settings()
    return SQLDatabase(
        db_name=connection_settings['db_name'],
        host=connection_settings['host'],
        user=connection_settings['user'],
        password=connection_settings['password']
    )
