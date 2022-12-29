from aiogram import types

from framework.controller.message_tools import notify
from lib.language import localization
from project.types import ErrorDictInterface


async def chat_access_denied(call: types.CallbackQuery, message: types.Message, result_connection: ErrorDictInterface):
    if result_connection['error'] in ['unexpected', 'user_none']:
        error_trace = ['errors', result_connection['error']]
    else:
        error_trace = ['add_chat', 'errors', result_connection['error']]
    await notify(
        call, message, localization.get_message(error_trace, message.from_user.language_code),
        alert=True, button_text='cancel')
