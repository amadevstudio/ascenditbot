import json

from aiogram import types

from lib.telegram.aiogram.message_processor import call_and_message_accessed_processor
from pkg.config.routes import RouteMap

from pkg.service.user_storage import UserStorage


# TODO: put to middleware
def get_type(call: types.CallbackQuery):
    return json.loads(call.data).get("tp", "")


def user_state(message: types.Message):
    return UserStorage.curr_state(message.chat.id)


async def event_wrapper(route_type: str, entity: types.Message | types.CallbackQuery, *args, **kwargs):
    call, message = call_and_message_accessed_processor(entity)
    await RouteMap.get_route_prop(route_type, 'method')(call, message, *args, **kwargs)


async def event_action_wrapper(route_type: str, action_type: str, call: types.CallbackQuery, *args, **kwargs):
    call, message = call_and_message_accessed_processor(call)
    await RouteMap.get_route_action_prop(route_type, action_type, 'method')(call, message, *args, **kwargs)
