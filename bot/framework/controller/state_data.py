import json
from typing import Any

from framework.system import telegram_types

from pkg.service.user_storage import UserStorage
from pkg.system.logger import logger


def decode_call_data(call: telegram_types.CallbackQuery) -> dict[str, Any]:
    try:
        return json.loads(call.data)
    except Exception as e:
        logger.error(e)

    return {}


def get_local_state_data(message: telegram_types.Message, route: str):
    try:
        return UserStorage.get_user_state_data(message.chat.id, route)
    except json.decoder.JSONDecodeError:
        return {}


def get_state_data(
        call: telegram_types.CallbackQuery, message: telegram_types.Message, route: str) -> dict[str, Any]:
    try:
        state_data = UserStorage.get_user_state_data(message.chat.id, route)
    except json.decoder.JSONDecodeError:
        state_data = {}

    try:
        call_data = json.loads(call.data)
        if route != call_data.get('tp', None):
            call_data = {}
    except Exception:
        call_data = {}

    return state_data | call_data
