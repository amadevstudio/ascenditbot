from typing import Callable, Dict, Any, Awaitable

from framework.controller import message_tools
from framework.system import telegram_types

from aiogram import BaseMiddleware, types

from framework.controller import state_navigator
from pkg.service.user_storage import UserStorage


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


class ReplyMarkupCleaner(BaseMiddleware):
    async def __call__(
            self, handler: Callable[[telegram_types.Message, Dict[str, Any]], Awaitable[Any]],
            entity: telegram_types.Message | telegram_types.CallbackQuery,
            data: dict[str, Any]):

        if isinstance(entity, telegram_types.Message):
            message = entity
            is_command = message_tools.is_command(entity.text)
        else:
            message = entity.message
            is_command = False

        if is_command or UserStorage.should_resend(message.chat.id):
            remover = await message.answer(text=".", reply_markup=types.ReplyKeyboardRemove())
            await remover.delete()

        return await handler(entity, data)
