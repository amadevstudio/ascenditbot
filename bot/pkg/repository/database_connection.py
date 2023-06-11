import asyncio
import re
import time
from datetime import datetime, timezone
from typing import Any, Literal, Generator, Dict

import asyncpg

from lib.python.singleton import Singleton
from pkg.system.logger import logger

Connection = asyncpg.connection.Connection
Cursor = asyncpg.connection.cursor.Cursor


class Database(metaclass=Singleton):
    def __init__(self):
        self.__max_connections = 1
        self.__connection_pool: asyncpg.Pool | None = None

    async def connect(self, config: dict[str, str] = None):
        if config is not None:
            self.__connection_pool = await asyncpg.create_pool(
                min_size=1,
                max_size=self.__max_connections,
                host=config['host'],
                database=config['database'],
                user=config['user'],
                password=config['password'])
        else:
            raise Exception("Database config is None")

    def get_connection(self) -> asyncpg.pool.PoolAcquireContext:
        # while True:
        #     try:
        return self.__connection_pool.acquire()
        #     except asyncpg.exceptions.PoolError as e:
        #         logger.warning("Not enough connections:", e)
        #         asyncio.sleep(1)

    @staticmethod
    def __prepare_query(query: str):
        """
        "  select %s from %s  " -> "select $1 from $2"
        @param query: Sql query
        """
        return ''.join([(r + f"${i + 1}") if r != "" else "" for i, r in enumerate(query.strip().split("%s"))])

    # Data helpers

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
        model['updated_at'] = utc_dt.replace(tzinfo=None)
        return model

    @staticmethod
    def inject_timestamps(model):
        model = Database.inject_updated_at(model)
        model['created_at'] = model['updated_at']
        return model

    # Query executors

    async def __query_executor(
            self, cursor_method: Literal['fetchone', 'fetchall'], query: str, params: tuple | dict | None
    ) -> Any:  # List[Dict], Dict, Cursor, None,
        try:
            query = self.__prepare_query(query)
            connection: asyncpg.connection.Connection
            if params is None:
                params = []
            async with self.get_connection() as connection:
                if cursor_method == 'fetchone':
                    return await connection.fetchrow(query, *params)
                elif cursor_method == 'fetchall':
                    return await connection.fetch(query, *params)
        except Exception as e:
            logger.error(e)
            return None

    async def fetchall(self, query: str, params: tuple | dict | None = None):
        result = await self.__query_executor('fetchall', query, params)
        return result if result is not None else []

    async def fetchone(self, query: str, params: tuple | dict | None = None):
        result = await self.__query_executor('fetchone', query, params)
        return result

    async def fetchmany(self, query: str, per: int, params: tuple | dict | None = None) \
            -> Generator[Dict, None, None]:
        connection: asyncpg.connection.Connection
        cursor: asyncpg.connection.cursor.Cursor
        query = self.__prepare_query(query)
        async with self.get_connection() as connection:
            async with connection.transaction():
                if params is None:
                    params = []
                cursor = await connection.cursor(query, *params)
                while True:
                    result = await cursor.fetch(per)
                    yield result
                    if not result:
                        break

    async def update_many(self, query: str, per: int, params: tuple | dict = None,
                          connection: asyncpg.connection.Connection | None = None) -> Generator[Any, None, None]:

        query = self.__prepare_query(query)

        transaction: asyncpg.connection.transaction.Transaction | None = None

        # If the connection is not created outside, create it and transaction
        if connection is None:
            commit = True
            connection = await self.get_connection()
            transaction = connection.transaction()
            await transaction.start()
        else:
            commit = False
        cursor: asyncpg.connection.cursor.Cursor

        try:
            if params is None:
                params = []
            cursor = await connection.cursor(query, *params)
            while True:
                result = await cursor.fetch(per)
                yield result

                if not result:
                    break

        except Exception as e:
            logger.error(e)
            # Rollback only if the transaction created locally
            if commit:
                await transaction.rollback()

        else:
            # Commit only if the transaction created locally
            if commit:
                await transaction.commit()

        finally:
            # Release connection only if created locally
            if commit:
                await self.__connection_pool.release(connection)

    async def execute_single_model(
            self, query: str, params: tuple = None, returning: str = None,
            connection: asyncpg.connection.Connection | None = None) -> dict | None:
        query = self.__prepare_query(query)

        # If the connection is not created outside, create it and transaction
        if connection is None:
            commit = True
            connection = await self.get_connection()
        else:
            commit = False

        if returning is not None:
            query += f" RETURNING {returning}"

        try:
            row_returning = await connection.fetchrow(query, *params)

            if returning is None:
                row_returning = None

            return row_returning

        except Exception as e:
            logger.error(e)

        finally:
            if commit:
                await self.__connection_pool.release(connection)

    async def find_model(self, model_name: str, model_data: dict[str, Any]):
        key_fields = list(model_data.keys())

        filled_key_fields = Database.__preset_key_fields(key_fields)

        query = "SELECT * FROM {model_name} WHERE {key_fields}".format(
            model_name=model_name,
            key_fields=(' AND '.join([f"{c} = %s" for c in filled_key_fields]))
        )

        key_fields_values = Database.__key_fields_values(filled_key_fields, model_data)

        return await self.fetchone(query, tuple(key_fields_values))

    async def insert_model(  # or update on conflict
            self, model_name: str, model_data: dict[str, Any],
            connection: asyncpg.connection.Connection | None = None,
            conflict_unique_fields: list[str] | None = None):

        model_data = self.__class__.inject_timestamps(model_data)

        query = """
            INSERT INTO {model_name} ({columns}) VALUES ({sss})
        """.format(
            model_name=model_name, columns=(', '.join(model_data.keys())),
            sss=(', '.join([f"%s" for _ in range(0, len(model_data))])))

        query_values = tuple(model_data.values())

        if conflict_unique_fields is not None:
            query += """
                ON CONFLICT ({conflict_fields}) DO UPDATE SET {columns_equal_values}
            """.format(
                conflict_fields=', '.join(conflict_unique_fields),
                columns_equal_values=(', '.join([f"{c} = %s" for c in model_data.keys()])))
            query_values *= 2

        return await self.execute_single_model(query, query_values, returning='*', connection=connection)

    async def update_model(
            self, model_name: str, model_data: dict[str, Any], key_fields: list[str] | None = None,
            connection: asyncpg.connection.Connection | None = None):
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

        return await self.execute_single_model(
            query, tuple(model_data_without_key_fields.values()) + tuple(key_fields_values), returning='*',
            connection=connection)

    async def delete_model(self, model_name: str, model_keys_data: dict[str, Any],
                           connection: asyncpg.connection.Connection | None = None):
        filled_key_fields = Database.__preset_key_fields(list(model_keys_data.keys()))

        query = """
            DELETE FROM {model_name} WHERE {key_fields}
        """.format(
            model_name=model_name,
            key_fields=(' AND '.join([f"{c} = %s" for c in filled_key_fields]))
        )

        key_fields_values = Database.__key_fields_values(filled_key_fields, model_keys_data)

        return await self.execute_single_model(
            query, tuple(key_fields_values), returning='*', connection=connection)
