from typing import TypedDict, Any, Callable, Awaitable, Protocol

from framework.system import telegram_types
from pkg.config.routes_dict import AvailableRoutes


class ControllerParams(TypedDict):
    call: telegram_types.CallbackQuery | None
    message: telegram_types.Message
    route_name: AvailableRoutes
    state_data: dict[str, Any]
    is_step_back: bool

    go_back_action: Callable  # [[telegram_types.CallbackQuery, AvailableRoutes], Awaitable]

    language_code: str | None
