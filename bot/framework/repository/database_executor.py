import asyncio
import concurrent.futures
import functools
from typing import Callable, Any, Generator

from lib.python.singleton import Singleton


class DatabaseExecutor(metaclass=Singleton):
    # def __init__(self):
    #     self.__max_connections = 10
    #     self.__executor_pool = concurrent.futures.ProcessPoolExecutor(max_workers=self.__max_connections)

    async def run(self, func: Callable, *args, **kwargs) -> Any:
        partial = functools.partial(func, *args, **kwargs)
        return await partial()
        # return await asyncio.get_event_loop().run_in_executor(self.__executor_pool, partial)  # psycopg2

    async def run_generator(self, func: Callable, *args, **kwargs) -> Generator[Any, None, None]:
        partial = functools.partial(func, *args, **kwargs)
        async for value in partial():
            yield value


databaseExecutor = DatabaseExecutor()
