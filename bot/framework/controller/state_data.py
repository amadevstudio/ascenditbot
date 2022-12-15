import json

from aiogram import types

from pkg.service.user_storage import UserStorage


def get_current_state_data(call: types.CallbackQuery, message: types.Message, route: str):
    try:
        state_data = UserStorage.get_user_state_data(message.chat.id, route)
    except json.decoder.JSONDecodeError:
        state_data = {}

    try:
        call_data = json.loads(call.data)
    except:
        call_data = {}

    return state_data | call_data
