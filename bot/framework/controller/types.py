from typing import TypedDict

from framework.system import telegram_types


class ControllerParams(TypedDict):
    call: telegram_types.CallbackQuery | None
    message: telegram_types.Message
    language_code: str
