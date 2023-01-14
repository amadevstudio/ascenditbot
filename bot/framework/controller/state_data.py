import json
from typing import Any

from aiogram import types

from pkg.service.user_storage import UserStorage
from pkg.system.logger import logger


def decode_call_data(call: types.CallbackQuery) -> dict[str, Any]:
    try:
        return json.loads(call.data)
    except Exception as e:
        logger.error(e)
        pass

    return {}


def get_current_state_data(call: types.CallbackQuery, message: types.Message, route: str) -> dict[str, Any]:
    try:
        state_data = UserStorage.get_user_state_data(message.chat.id, route)
    except json.decoder.JSONDecodeError:
        state_data = {}

    try:
        call_data = json.loads(call.data)
    except Exception:
        call_data = {}

    return state_data | call_data
