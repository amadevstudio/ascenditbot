import json

from aiogram import types

from lib.language import localization
from pkg.config.config import empty_photo_link
from pkg.controller.message_sender import message_sender

from pkg.service import user_storage


async def start(call: types.CallbackQuery, message: types.Message, change_user_state=True):
    if call is None:
        await message.reply('👋')

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
    button = types.InlineKeyboardButton(
        localization.get_message(["buttons", "back"], message.from_user.language_code),
        callback_data=json.dumps({'tp': 'bck'}))
    markup = types.InlineKeyboardMarkup().add(button)

    message_structures = [{
        'type': 'text',
        'text': localization.get_message(["menu", "menu"], message.from_user.language_code),
        'reply_markup': markup,
    }, {
        'type': 'image',
        'image_url': empty_photo_link
    }]
    await message_sender(message, resending=call is None, message_structures=message_structures)

    if change_user_state:
        user_storage.change_page(call.message.chat.id, 'menu')
