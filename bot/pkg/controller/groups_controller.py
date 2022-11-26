from aiogram import types

from lib.language import localization
from pkg.controller.message_tools import message_sender, go_back_inline_markup
from pkg.service import user_storage


async def add_group(call: types.CallbackQuery, message: types.Message, change_user_state=True):
    message_structures = [{
        'type': 'text',
        'text': localization.get_message(["add_group", "instruction"], message.from_user.language_code),
        'reply_markup': go_back_inline_markup(message.from_user.language_code)
    }]
    await message_sender(message, resending=call is None, message_structures=message_structures)

    if change_user_state:
        user_storage.change_page(message.chat.id, 'menu')
