from datetime import datetime, timezone

import psycopg2
from psycopg2.extras import RealDictCursor

from lib.python.singleton import Singleton
from pkg.system.logger import logger


class Database(metaclass=Singleton):
    def __init__(self):
        self.connection = None

    def connect(self, config: dict[str, str] = None):
        if config is not None:
            self.connection = psycopg2.connect(
                host=config['host'],
                database=config['database'],
                user=config['user'],
                password=config['password'])
        else:
            self.connection = psycopg2.connect()

    def _build_cursor(self):
        return self.connection.cursor(cursor_factory=RealDictCursor)

    def find(self, model: str, id: int):
        query = "SELECT * FROM {model} WHERE id = %s".format(model=model)
        return self.fetchone(query, (id,))

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

    def execute(self, query: str, params: tuple, cursor: psycopg2.extensions.cursor = None):
        if cursor is None:
            cursor = self._build_cursor()
        try:
            cursor.execute(query + " RETURNING id", params)
            row_id = cursor.fetchone()['id']
            self.connection.commit()
            return row_id, cursor
        except psycopg2.DatabaseError as e:
            self.connection.rollback()
            logger.err(f"Can't register user: {e}")
            return None, None

    def commit(self, query: str, params: tuple, cursor: psycopg2.extensions.cursor = None, returning='id'):
        if cursor is None:
            cursor = self._build_cursor()

        try:
            cursor.execute(query + f" RETURNING {returning}", params)
            row_returning = cursor.fetchone()[returning]
            self.connection.commit()
            return row_returning
        except psycopg2.DatabaseError as e:
            self.connection.rollback()
            logger.err(f"Can't register user: {e}")
            return None
        finally:
            cursor.close()

    @staticmethod
    def cursor_creator(func):
        def _wrap(self, *args, **kwargs):
            try:
                cursor = self._build_cursor()
                return func(self, *args, **kwargs, cursor=cursor)
            finally:
                if cursor:
                    cursor.close()

        return _wrap

    @cursor_creator
    def fetchall(self, query: str, params: tuple, cursor):
        cursor.execute(query, params)
        return cursor.fetchall()

    @cursor_creator
    def fetchone(self, query: str, params: tuple, cursor):
        cursor.execute(query, params)
        return cursor.fetchone()

    def insert_model(
            self, model_name: str, model_data: dict, commit: bool = True, cursor: psycopg2.extensions.cursor = None):
        model_data = self.__class__.inject_timestamps(model_data)

        query = """
            INSERT INTO {model_name} ({columns}) VALUES ({sss})
        """.format(
            model_name=model_name, columns=(', '.join(model_data.keys())),
            sss=(', '.join(["%s" for _ in range(0, len(model_data))])))

        if commit:
            model_id = self.commit(query, tuple(model_data.values()), cursor=cursor)
            return self.fetchone(f"SELECT * FROM {model_name} WHERE id = %s", (model_id,))

        else:
            model_id, cursor = self.execute(query, tuple(model_data.values()), cursor=cursor)
            return self.fetchone(f"SELECT * FROM {model_name} WHERE id = %s", (model_id,)), cursor

    def update_model(self, model_name: str, model_data: dict):
        model_data = self.__class__.inject_updated_at(model_data)
        model_id = model_data.pop('id')

        query = """
            UPDATE {model_name} SET {columns_equal_values} WHERE id = %s
        """.format(
            model_name=model_name, columns_equal_values=(', '.join([f"{c} = %s" for c in model_data.keys()])))

        model_id = self.commit(query, tuple(model_data.values()) + (model_id,))

        return self.fetchone(f"SELECT * FROM {model_name} WHERE id = %s", (model_id,))
