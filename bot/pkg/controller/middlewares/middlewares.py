from typing import Callable, Dict, Any, Awaitable

from framework.controller import message_tools
from framework.controller.router_tools import get_type
from framework.controller.state_data import get_state_data
from framework.system import telegram_types

from aiogram import BaseMiddleware, types

from framework.controller import state_navigator
from lib.language import localization
from pkg.config.routes import RouteMap
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
            is_call, go_back_action = False, False
            message = entity
            is_command = message_tools.is_command(entity.text)
        else:
            is_call = True
            go_back_action = (get_type(entity) == 'back')
            message = entity.message
            is_command = False

        curr = UserStorage.curr_state(message.chat.id)
        may_have_under_keyboard = curr is None or RouteMap.get_route_prop(curr, 'have_under_keyboard') is True

        if may_have_under_keyboard and (
                is_command or UserStorage.should_resend(message.chat.id)
                or (is_call and not go_back_action)):
            remover = await message.answer(
                text=localization.get_emoji('hourglass'), reply_markup=types.ReplyKeyboardRemove())
            await remover.delete()

        return await handler(entity, data)
