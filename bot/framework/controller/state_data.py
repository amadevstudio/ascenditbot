import json
from typing import Any

from framework.system import telegram_types
from pkg.config.routes_dict import AvailableRoutes

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
        call: telegram_types.CallbackQuery | None,
        message: telegram_types.Message,
        route: AvailableRoutes,
        action: str | None = None
) -> dict[str, Any]:
    # 1. Смена маршрута: данные маршрута (пустые) + call (так как tp равен маршруту)
    # 2. Экшен: данные маршрута + call (без tp, мутация)
    # 3. Назад: данные маршрута + call (пустой, так как tp не равен маршруту)
    # 4. Валидации: данные маршрута (пустые или нет) + call (пустой, если кнопка не маршрута)

    if call is None:
        call_data = {}
    else:
        try:
            call_data = json.loads(call.data)
        except json.decoder.JSONDecodeError:
            call_data = {}

        # Если не действие (смена маршрута, назад, валидации)
        if action is None:
            # То учитывать только call_data для этого же маршрута
            if call_data['tp'] != route:
                call_data = {}
        # Если действие, примешать к состоянию, удалив tp
        else:
            del call_data['tp']

    try:
        state_data = UserStorage.get_user_state_data(message.chat.id, route)
    except json.decoder.JSONDecodeError:
        state_data = {}

    return state_data | call_data
