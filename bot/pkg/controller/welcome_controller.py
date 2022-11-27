import json

from aiogram import types

from lib.language import localization
from framework.controller.message_tools import message_sender

from pkg.service import user_storage, user


async def start(call: types.CallbackQuery, message: types.Message, change_user_state=True):
    if call is None:
        await message.reply('👋')
        user.register(message.chat.id, message.from_user.language_code)

    button = types.InlineKeyboardButton(localization.get_message(
        ["welcome", "let's begin"], message.from_user.language_code), callback_data=json.dumps({'tp': 'menu'}))
    markup = types.InlineKeyboardMarkup().add(button)

    message_structures = [{
        'type': 'text',
        'text': localization.get_message(["welcome", "introduction"], message.from_user.language_code),
        'reply_markup': markup,
    }]
    await message_sender(message, resending=call is None, message_structures=message_structures)

    if change_user_state:
        user_storage.new_navigation_journey(message.chat.id, 'start')


async def menu(call: types.CallbackQuery, message: types.Message, change_user_state=True):
    buttons = []
    for button_type in ["add_group", "my_groups", "help", "payment"]:
        buttons.append(types.InlineKeyboardButton(
            localization.get_message(["buttons", button_type], message.from_user.language_code),
            callback_data=json.dumps({'tp': button_type})))
    markup = types.InlineKeyboardMarkup().row(buttons[0], buttons[1])
    markup.row(buttons[2], buttons[3])

    message_structures = [{
        'type': 'text',
        'text': localization.get_message(["menu", "menu"], message.from_user.language_code),
        'reply_markup': markup,
    }]
    await message_sender(message, resending=call is None, message_structures=message_structures)

    if change_user_state:
        user_storage.change_page(message.chat.id, 'menu')
