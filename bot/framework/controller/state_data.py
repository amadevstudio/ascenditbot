import json

from aiogram import types

from pkg.service.user_storage import UserStorage


def get_current_state_data(call: types.CallbackQuery, message: types.Message, route: str):
    try:
        return UserStorage.get_user_state_data(message.chat.id, route)
    except Exception:
        return json.loads(call.data)
