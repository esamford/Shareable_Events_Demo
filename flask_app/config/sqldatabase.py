import threading
import time
from typing import List

import pymysql


class SQLDatabase:
    # Use dictionaries to keep track of the connection information and waiting queues for each database file.
    __db_connection_settings = dict()
    __connections = dict()
    __wait_queues = dict()

    def __init__(self, db_name: str, host: str = 'localhost', user: str = 'root', password: str = 'root'):
        connection_settings = {
            'host': host,
            'user': user,
            'password': password,
            'charset': 'utf8mb4',
            'autocommit': False
        }
        self.__db_name = db_name
        self.__set_connection_settings(db_name, connection_settings)

    @classmethod
    def __set_connection_settings(cls, db_name: str, connection_settings: dict):
        cls.__db_connection_settings[db_name] = connection_settings

    @classmethod
    def __get_connection(cls, db_name: str) -> pymysql.Connection:
        assert isinstance(db_name, str)

        # Get this database file's waiting queue.
        if db_name not in cls.__wait_queues:
            cls.__wait_queues[db_name] = list()
        wait_queue = cls.__wait_queues[db_name]
        assert isinstance(wait_queue, list)

        # Add this thread's identifier to the queue and wait for it to be at position 0.
        thread_identifier = threading.current_thread().ident
        wait_queue.append(thread_identifier)
        while wait_queue[0] != thread_identifier:
            time.sleep(0.0001)

        # Wait for the currently-open connection to close.
        while db_name in cls.__connections:
            time.sleep(0.0001)

        # Create the new connection, then remove the thread's identifier from the waiting queue
        # so that the next thread in that queue can move to the second while loop above.
        if db_name not in cls.__db_connection_settings:
            raise Exception(
                "There was an error during class initialization. "
                "Database settings for '{}' were not set.".format(db_name)
            )
        connection_settings = cls.__db_connection_settings[db_name]
        cls.__connections[db_name] = pymysql.connect(
            db=db_name,

            host=connection_settings['host'],
            user=connection_settings['user'],
            password=connection_settings['password'],
            charset=connection_settings['charset'],
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=connection_settings['autocommit']
        )
        assert wait_queue.pop(0) == thread_identifier
        return cls.__connections[db_name]

    @classmethod
    def __close_connection(cls, db_name: str) -> None:
        assert isinstance(db_name, str)

        # If the connection exists, close it and allow for a new one to be opened.
        if db_name in cls.__connections:
            connection = cls.__connections[db_name]
            connection.close()
            del cls.__connections[db_name]

    @staticmethod
    def __get_cursor(connection: pymysql.Connection) -> pymysql.cursors.Cursor:
        cursor = connection.cursor()
        return cursor

    def execute_query(self, query: str, query_args: dict = {}) -> List[dict]:
        """
        :param query:
            The query string to execute. Any arguments that must be added to the string should be written
            as question marks.
        :param query_args:
            A list or tuple containing all arguments to be used within the query.
        :return:
            If this is a select statement, return a list of dictionaries (one for each record found) with
            keys matching the fields specified in the query. For any other statement, return an empty list.

        Examples:
            query:      "select * from users where id = %(id)s;"
            query_args: {'id': 1, }
            result:     [ {'id': 1, 'email': 'user_email@gmail.com', ...}, ]

            query:      "select * from users where email like '%%(email)s';
            query_args: {'email': 'gmail.com', }
            result:     [
                            {'id': 1, 'email': 'user_email@gmail.com', ...},
                            {'id': 124, 'email': 'new_email@gmail.com', ...},
                            {'id': 146, 'email': 'other_email@gmail.com', ...},
                            ...
                        ]
        """
        assert isinstance(query, str)
        assert isinstance(query_args, dict)

        connection = None
        try:
            connection = self.__get_connection(self.__db_name)
            cursor = self.__get_cursor(connection)
            cursor.execute(query, query_args)
            result = list(cursor.fetchall())
            connection.commit()
            return result
        except Exception as ex:
            if hasattr(connection, "rollback"):
                connection.rollback()
            raise ex
        finally:
            self.__close_connection(self.__db_name)

    def execute_insert(self, query: str, query_args: dict = {}) -> int:
        """
        :param query:
            The query string to execute. Any arguments that must be added to the string should be written
            as question marks.
        :param query_args:
            A dictionary containing all arguments to be used within the query.
        :return:
            Similar to execute_query(), but returns the ID number of the new record rather than a list of
            dictionaries.

        Example:
            query:      "insert into users (email, first_name, last_name, ...)
                         values (%(email)s, %(first_name)s, %(last_name)s, ...);"
            query_args: {'email': 'new_email@gmail.com', 'first_name': 'John', 'last_name': 'Smith', ...}
            result:     124  # With 124 being the new ID number for the record just created.
        """
        assert isinstance(query, str)
        assert isinstance(query_args, dict)

        connection = None
        try:
            connection = self.__get_connection(self.__db_name)
            cursor = self.__get_cursor(connection)
            cursor.execute(query, query_args)

            connection.commit()
            return int(cursor.lastrowid)
        except Exception as ex:
            if hasattr(connection, "rollback"):
                connection.rollback()
            raise ex
        finally:
            self.__close_connection(self.__db_name)


if __name__ == "__main__":
    db = SQLDatabase(db_name="belt_exam_2_schema")

    '''
    result = db.execute_insert(
        """
        INSERT INTO users (first_name, last_name, email, password)
        VALUES (
            'Peter', 'Smith', 'psmith@gmail.com', 'password2'
        );
        """,
        {'first_name': 'John'}
    )
    print(result, sep="\n")
    # '''

    result = db.execute_query(
        "SELECT * FROM users;"
    )
    print(*result, sep="\n")

