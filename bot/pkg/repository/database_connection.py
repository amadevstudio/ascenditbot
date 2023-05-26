import time
from datetime import datetime, timezone
from typing import Any, Literal, Generator

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

from lib.python.singleton import Singleton
from pkg.system.logger import logger


class Database(metaclass=Singleton):
    def __init__(self):
        self.connection_pool: psycopg2.pool.SimpleConnectionPool | None = None

    def connect(self, config: dict[str, str] = None):
        if config is not None:
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                minconn=1,
                maxconn=20,
                host=config['host'],
                database=config['database'],
                user=config['user'],
                password=config['password'])
        else:
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(minconn=1, maxconn=1)

    def build_connection(self) -> psycopg2.extensions.connection:
        while True:
            try:
                return self.connection_pool.getconn()
            except psycopg2.pool.PoolError:
                time.sleep(1)  # TODO: migrate to asyncio wrapper?

    @staticmethod
    def __build_cursor(connection: psycopg2.extensions.connection) -> psycopg2.extensions.cursor:
        return connection.cursor(cursor_factory=RealDictCursor)

    def close(self, connection: psycopg2.extensions.connection):
        try:
            self.connection_pool.putconn(connection)
        except Exception as e:
            logger.error(e)

    def commit_and_close(self, connection: psycopg2.extensions.connection):
        try:
            connection.commit()
            self.connection_pool.putconn(connection)
        except Exception as e:
            logger.error(e)

    def rollback_and_close(self, connection: psycopg2.extensions.connection):
        try:
            connection.rollback()
            self.connection_pool.putconn(connection)
        except Exception as e:
            logger.error(e)

    @staticmethod
    def __preset_key_fields(key_fields: list[str] | None):
        if key_fields is None:
            return ['id']

        return key_fields

    @staticmethod
    def __key_fields_values(filled_key_fields: list[str], model_data: dict[str, Any]):
        key_fields_values = []
        for key_field in filled_key_fields:
            key_fields_values.append(model_data[key_field])
        return key_fields_values

    @staticmethod
    def inject_updated_at(model):
        utc_dt = datetime.now(timezone.utc)  # UTC time
        model['updated_at'] = utc_dt.astimezone()
        return model

    @staticmethod
    def inject_timestamps(model):
        model = Database.inject_updated_at(model)
        model['created_at'] = model['updated_at']
        return model

    def __query_executor(
            self, cursor_method: Literal['fetchone', 'fetchall'], query: str, params: tuple | dict
    ) -> Any:  # List[Dict], Dict, Cursor, None,
        connection = self.build_connection()
        try:
            with self.__build_cursor(connection) as cursor:
                cursor.execute(query, params)
                if cursor_method == 'fetchone':
                    return cursor.fetchone()
                elif cursor_method == 'fetchall':
                    return cursor.fetchall()
        except Exception as e:
            logger.error(e)
            if cursor is not None:
                connection.rollback()
            return None
        finally:
            self.close(connection)

    def fetchall(self, query: str, params: tuple | dict = None):
        result = self.__query_executor('fetchall', query, params)
        return result if result is not None else []

    def fetchone(self, query: str, params: tuple | dict = None):
        result = self.__query_executor('fetchone', query, params)
        return result

    def fetchmany(self, query: str, per: int, params: tuple | dict = None):
        connection = self.build_connection()
        with self.__build_cursor(connection) as cursor:
            cursor.execute(query, params)
            while True:
                result = cursor.fetchmany(per)
                yield result
                if not result:
                    self.close(connection)
                    break

    def update_many(self, query: str, per: int, params: tuple | dict = None,
                    connection: psycopg2.extensions.connection | None = None) -> Generator[Any, None, None]:
        if connection is None:
            commit = True
            connection = self.build_connection()
        else:
            commit = False

        try:
            with self.__build_cursor(connection) as cursor:
                cursor.execute(query, params)
                while True:
                    result = cursor.fetchmany(per)
                    yield result
                    if not result:
                        break

        except psycopg2.DatabaseError as e:
            logger.error(e)
            if commit:
                self.rollback_and_close(connection)
            return None
        finally:
            if commit:
                self.commit_and_close(connection)

    def execute_single_model(
            self, query: str, params: tuple = None, returning: str = None,
            connection: psycopg2.extensions.connection | None = None) -> dict | None:

        if connection is None:
            commit = True
            connection = self.build_connection()
        else:
            commit = False

        if returning is not None:
            query += f" RETURNING {returning}"

        try:
            with self.__build_cursor(connection) as cursor:
                cursor.execute(query, params)

                if returning is not None:
                    row_returning = cursor.fetchone()
                else:
                    row_returning = None

                return row_returning

        except psycopg2.DatabaseError as e:
            logger.error(e)
            if commit:
                self.rollback_and_close(connection)
            return None

        finally:
            if commit:
                self.commit_and_close(connection)

    def find_model(self, model_name: str, model_data: dict[str, Any]):
        key_fields = list(model_data.keys())

        filled_key_fields = Database.__preset_key_fields(key_fields)

        query = "SELECT * FROM {model_name} WHERE {key_fields}".format(
            model_name=model_name,
            key_fields=(' AND '.join([f"{c} = %s" for c in filled_key_fields]))
        )

        key_fields_values = Database.__key_fields_values(filled_key_fields, model_data)

        return self.fetchone(query, tuple(key_fields_values))

    def insert_model(  # or update on conflict
            self, model_name: str, model_data: dict[str, Any],
            connection: psycopg2.extensions.connection | None = None,
            conflict_unique_fields: list[str] | None = None):

        model_data = self.__class__.inject_timestamps(model_data)

        query = """
            INSERT INTO {model_name} ({columns}) VALUES ({sss})
        """.format(
            model_name=model_name, columns=(', '.join(model_data.keys())),
            sss=(', '.join(["%s" for _ in range(0, len(model_data))])))

        query_values = tuple(model_data.values())

        if conflict_unique_fields is not None:
            query += """
                ON CONFLICT ({conflict_fields}) DO UPDATE SET {columns_equal_values}
            """.format(
                conflict_fields=', '.join(conflict_unique_fields),
                columns_equal_values=(', '.join([f"{c} = %s" for c in model_data.keys()])))
            query_values *= 2

        return self.execute_single_model(query, query_values, returning='*', connection=connection)

    def update_model(
            self, model_name: str, model_data: dict[str, Any], key_fields: list[str] | None = None,
            connection: psycopg2.extensions.connection | None = None):
        model_data = self.__class__.inject_updated_at(model_data)

        # Set key fields as ['id'] if empty
        filled_key_fields = Database.__preset_key_fields(key_fields)

        # Get key fields values
        key_fields_values = Database.__key_fields_values(filled_key_fields, model_data)

        # Remove key fields from update list
        model_data_without_key_fields = {**model_data}
        for key_field in filled_key_fields:
            model_data_without_key_fields.pop(key_field)

        query = """
            UPDATE {model_name} SET {columns_equal_values} WHERE {key_fields}
        """.format(
            model_name=model_name,
            columns_equal_values=(', '.join([f"{c} = %s" for c in model_data_without_key_fields.keys()])),
            key_fields=(' AND '.join([f"{c} = %s" for c in filled_key_fields]))
        )

        return self.execute_single_model(
            query, tuple(model_data_without_key_fields.values()) + tuple(key_fields_values), returning='*',
            connection=connection)

    def delete_model(self, model_name: str, model_keys_data: dict[str, Any],
                     connection: psycopg2.extensions.connection | None = None):
        filled_key_fields = Database.__preset_key_fields(list(model_keys_data.keys()))

        query = """
            DELETE FROM {model_name} WHERE {key_fields}
        """.format(
            model_name=model_name,
            key_fields=(' AND '.join([f"{c} = %s" for c in filled_key_fields]))
        )

        key_fields_values = Database.__key_fields_values(filled_key_fields, model_keys_data)

        return self.execute_single_model(
            query, tuple(key_fields_values), returning='*', connection=connection)


class DatabaseContextManager:
    def __init__(self, db: Database):
        self.db = db

    def __enter__(self):
        self.connection = self.db.build_connection()
        return self.connection

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val:  # Error occurred
            self.db.rollback_and_close(connection=self.connection)
        else:
            self.db.commit_and_close(connection=self.connection)
