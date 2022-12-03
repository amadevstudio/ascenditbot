from aiogram import types
from aiogram.dispatcher.middlewares import BaseMiddleware

from framework.controller import state_navigator


class NoWhereInputProcessorMiddleware(BaseMiddleware):
    def __init__(self):
        super(NoWhereInputProcessorMiddleware, self).__init__()

    # async def on_process_update(self, update: types.Update (call or message), data: dict):
    async def on_pre_process_message(self, message: types.Message, data: dict):
        # handler = current_handler.get()
        # dispatcher = Dispatcher.get_current()

        # data["some_param"] = "Данные"
        # Using: @dispatcher; async def handler(message, middleware_data)

        state_navigator.nowhere_input_processor(message)

        # raise CancelHandler()
