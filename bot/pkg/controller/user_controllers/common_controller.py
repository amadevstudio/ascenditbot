from typing import Literal

from framework.system import telegram_types

from framework.controller.message_tools import notify
from lib.language import localization
from project.types import ErrorDictInterface


async def raise_error(
        call: telegram_types.CallbackQuery | None, message: telegram_types.Message,
        raised_type: Literal['user_none', 'unexpected', 'state_data_none'],
        alert: bool = True, button_text: Literal['back', 'cancel'] = 'back'
):
    error_trace = ['errors', raised_type]

    await notify(
        call, message, localization.get_message(error_trace, message.from_user.language_code),
        alert=alert, button_text=button_text)


async def chat_access_denied(call: telegram_types.CallbackQuery, message: telegram_types.Message, result_connection: ErrorDictInterface):
    if result_connection['error'] in ['unexpected', 'user_none']:
        error_trace = ['errors', result_connection['error']]
    else:
        error_trace = ['access', 'chat', 'errors', result_connection['error']]
    await notify(
        call, message, localization.get_message(error_trace, message.from_user.language_code),
        alert=True, button_text='cancel')
