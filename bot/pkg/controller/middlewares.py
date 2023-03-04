from typing import Callable, Dict, Any, Awaitable

from aiogram import types, BaseMiddleware
from aiogram.types import Message

from framework.controller import state_navigator


class NoWhereInputProcessorMiddleware(BaseMiddleware):
    # async def on_process_update(self, update: types.Update (call or message), data: dict):
    async def __call__(
            self, handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            message: types.Message, data: dict):
        # handler = current_handler.get()
        # dispatcher = Dispatcher.get_current()

        # data["some_param"] = "Данные"
        # Using: @dispatcher; async def handler(message, middleware_data)

        state_navigator.nowhere_input_processor(message)
        return await handler(message, data)

        # raise CancelHandler()
