from datetime import datetime, timezone
from typing import Any, Literal

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

    def build_cursor(self):
        return self.connection.cursor(cursor_factory=RealDictCursor)

    @staticmethod
    def close_cursor(cursor):
        if cursor is not None:
            cursor.close()

    @staticmethod
    def _preset_key_fields(key_fields: list[str] | None):
        if key_fields is None:
            return ['id']

        return key_fields

    @staticmethod
    def _key_fields_values(filled_key_fields: list[str], model_data: dict[str, Any]):
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

    def execute(
            self, query: str, params: tuple, commit=True, cursor=None, keep_cursor=False,
            returning=None) -> dict | None:
        if cursor is None:
            cursor = self.build_cursor()

        if returning is not None:
            query += f" RETURNING {returning}"

        try:
            cursor.execute(query, params)

            row_returning = cursor.fetchone()

            if commit:
                self.connection.commit()

            return row_returning

        except psycopg2.DatabaseError as e:
            self.connection.rollback()
            logger.err(f"Can't commit: {e}")
            return None

        finally:
            if not keep_cursor:
                cursor.close()

    def _query_executor(
            self, cursor_method: Literal['fetchone', 'fetchall', 'fetchmany'], query: str, params: tuple
    ) -> Any:  # List[Dict], Dict, Cursor, None,
        cursor = None
        try:
            cursor = self.build_cursor()
            cursor.execute(query, params)
            if cursor_method == 'fetchone':
                return cursor.fetchone()
            elif cursor_method == 'fetchall':
                return cursor.fetchall()
            elif cursor_method == 'fetchmany':
                return cursor
        except Exception as e:
            logger.err(e)
            self.connection.rollback()
            return None
        finally:
            if cursor is not None and cursor_method != 'fetchmany':
                cursor.close()

    def fetchall(self, query: str, params: tuple = None):
        result = self._query_executor('fetchall', query, params)
        return result if result is not None else []

    def fetchone(self, query: str, params: tuple = None):
        result = self._query_executor('fetchone', query, params)
        return result

    def fetchmany(self, query: str, per: int, params: tuple = None):
        cursor = self._query_executor('fetchmany', query, params)
        while True:
            result = cursor.fetchmany(per)
            yield result
            if not result:
                cursor.close()
                break

    def find_model(self, model_name: str, model_data: dict[str, Any], key_fields: list[str] | None = None):
        filled_key_fields = Database._preset_key_fields(key_fields)

        query = "SELECT * FROM {model_name} WHERE {key_fields}".format(
            model_name=model_name,
            key_fields=(' AND '.join([f"{c} = %s" for c in filled_key_fields]))
        )

        key_fields_values = Database._key_fields_values(filled_key_fields, model_data)

        return self.fetchone(query, tuple(key_fields_values))

    def insert_model(  # or update on conflict
            self, model_name: str, model_data: dict[str, Any], commit: bool = True,
            cursor=None, keep_cursor=False, conflict_unique_fields: list[str] | None = None):

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

        return self.execute(query, query_values, commit=commit, cursor=cursor, keep_cursor=keep_cursor, returning='*')

    def update_model(self, model_name: str, model_data: dict[str, Any], key_fields: list[str] | None = None):
        model_data = self.__class__.inject_updated_at(model_data)

        filled_key_fields = Database._preset_key_fields(key_fields)

        query = """
            UPDATE {model_name} SET {columns_equal_values} WHERE {key_fields}
        """.format(
            model_name=model_name,
            columns_equal_values=(', '.join([f"{c} = %s" for c in model_data.keys()])),
            key_fields=(' AND '.join([f"{c} = %s" for c in filled_key_fields]))
        )

        key_fields_values = Database._key_fields_values(filled_key_fields, model_data)

        return self.execute(query, tuple(model_data.values()) + tuple(key_fields_values), returning='*')
