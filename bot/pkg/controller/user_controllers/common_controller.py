from typing import Literal

from framework.system import telegram_types

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from framework.controller.message_tools import notify, user_language
from framework.system.bot_setup import bot
from lib.language import localization
from project.i18n_owner_tools import ADD_TO_GROUP_URL
from project.types import ErrorDictInterface

# The bot lost its rights or was removed: the owner can fix it in one tap, so say how instead of a bare alert
_RIGHTS_ERRORS = {'not_admin': 'no_rights', 'cant_edit_messages': 'no_rights', 'not_member': 'not_member'}


async def raise_error(
        call: telegram_types.CallbackQuery | None, message: telegram_types.Message,
        raised_type: Literal['user_none', 'unexpected', 'state_data_none'],
        alert: bool = True, button_text: Literal['back', 'cancel'] = 'back'
):
    error_trace = ['errors', raised_type]

    await notify(
        call, message, localization.get_message(error_trace, user_language(call, message)),
        alert=alert, button_text=button_text)


async def chat_access_denied(call: telegram_types.CallbackQuery, message: telegram_types.Message, result_connection: ErrorDictInterface):
    if result_connection['error'] in _RIGHTS_ERRORS:
        language_code = user_language(call, message)
        if call is not None:
            await bot.answer_callback_query(callback_query_id=call.id)
        await bot.send_message(
            message.chat.id, localization.get_message(
                ['access', 'chat', 'fix_rights', _RIGHTS_ERRORS[result_connection['error']]], language_code),
            parse_mode='HTML', reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(
                text=localization.get_message(['group', 'give_rights_button'], language_code),
                url=ADD_TO_GROUP_URL)]]))
        return
    if result_connection['error'] in ['unexpected', 'user_none']:
        error_trace = ['errors', result_connection['error']]
    else:
        error_trace = ['access', 'chat', 'errors', result_connection['error']]
    await notify(
        call, message, localization.get_message(error_trace, user_language(call, message)),
        alert=True, button_text='cancel')
