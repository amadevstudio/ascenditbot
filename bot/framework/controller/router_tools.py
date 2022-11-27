import json

from aiogram import types

from lib.telegram.aiogram.message_processor import call_and_message_accessed_processor
from pkg.config.routes import RouteMap

from pkg.service import user_storage


def get_type(call: types.CallbackQuery):
    return json.loads(call.data).get("tp", "")


def user_state(message: types.Message):
    return user_storage.curr_state(message.chat.id)


async def event_wrapper(type: str, entity: types.Message | types.CallbackQuery):
    call, message = call_and_message_accessed_processor(entity)
    await RouteMap.get_route(type, 'method')(call, message)
