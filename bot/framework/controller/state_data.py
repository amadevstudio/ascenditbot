import json

from aiogram import types

from pkg.service.user_storage import UserStorage


def get_current_state_data(call: types.CallbackQuery, message: types.Message, route: str):
    try:
        state_data = UserStorage.get_user_state_data(message.chat.id, route)
    except json.decoder.JSONDecodeError:
        state_data = None

    if state_data is None:
        state_data = json.loads(call.data)

    return state_data
