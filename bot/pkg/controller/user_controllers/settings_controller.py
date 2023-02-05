import json

from aiogram import types

from framework.controller.message_tools import message_sender
from lib.language import localization
from pkg.config import routes
from pkg.service.user_storage import UserStorage


async def page(call: types.CallbackQuery, message: types.Message, change_user_state=True):
    print("HERE")
    reply_markup = types.InlineKeyboardMarkup()
    reply_markup.add(types.InlineKeyboardButton(
        localization.get_message(['settings', 'buttons', 'email'], message.from_user.language_code),
        callback_data=json.dumps({'tp': routes.RouteMap.type('settings_email')})
    ))

    message_structures = [{
        'type': 'text',
        'text': localization.get_message(['settings', 'page'], message.from_user.language_code),
        'reply_markup': reply_markup,
    }]
    await message_sender(message, resending=call is None, message_structures=message_structures)

    if change_user_state:
        UserStorage.new_navigation_journey(message.chat.id, routes.RouteMap.type('settings'))


async def email(call: types.CallbackQuery, message: types.Message, change_user_state=True):
    pass
