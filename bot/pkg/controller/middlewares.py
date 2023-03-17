from typing import Callable, Dict, Any, Awaitable
from framework.system import telegram_types

from aiogram import BaseMiddleware

from framework.controller import state_navigator


class NoWhereInputProcessorMiddleware(BaseMiddleware):
    # async def on_process_update(self, update: telegram_types.Update (call or message), data: dict):
    async def __call__(
            self, handler: Callable[[telegram_types.Message, Dict[str, Any]], Awaitable[Any]],
            message: telegram_types.Message,
            data: dict[str, Any]):
        # handler = current_handler.get()
        # dispatcher = Dispatcher.get_current()

        # data["some_param"] = "Данные"
        # Using: @dispatcher; async def handler(message, middleware_data)

        state_navigator.nowhere_input_processor(message)
        return await handler(message, data)

        # raise CancelHandler()
