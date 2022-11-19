import json

from aiogram import types

from lib import localization

async def start(message: types.Message):
    await message.reply('👋')

    button = types.InlineKeyboardButton('Начнём!', callback_data=json.dumps({'act': '/menu'}))
    markup = types.InlineKeyboardMarkup().add(button)
    await message.answer(
        localization.get_message(["welcome", "introduction"], message.from_user.language_code),
        reply_markup=markup)
