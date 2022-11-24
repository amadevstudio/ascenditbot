import json

from aiogram import types

from lib.language import localization
from lib.telegram.aiogram.message_processor import call_and_message_accessed_processor

from pkg.service import user_storage


async def start(call: types.CallbackQuery, message: types.Message, change_user_state=True):
    await message.reply('👋')

    button = types.InlineKeyboardButton(localization.get_message(
        ["welcome", "let's begin"], message.from_user.language_code), callback_data=json.dumps({'tp': 'menu'}))
    markup = types.InlineKeyboardMarkup().add(button)

    if call is None:
        await message.answer(
            localization.get_message(["welcome", "introduction"], message.from_user.language_code),
            reply_markup=markup)
    else:
        await message.edit_text(
            localization.get_message(["welcome", "introduction"], message.from_user.language_code),
            reply_markup=markup
        )

    if change_user_state:
        user_storage.new_navigation_journey(message.chat.id, 'start')


async def menu(call: types.CallbackQuery, message: types.Message, change_user_state=True):
    markup = types.InlineKeyboardMarkup().add(button)
    # TODO Use message master
    await call.message.edit_text(
        'Menu',
        reply_markup=markup)

    if change_user_state:
        user_storage.change_page(call.message.chat.id, 'menu')
