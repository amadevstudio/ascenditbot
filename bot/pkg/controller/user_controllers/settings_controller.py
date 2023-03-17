import json

from aiogram import types

from framework.controller.message_tools import message_sender, go_back_inline_markup, go_back_inline_button, \
    is_call_or_command
from lib.language import localization
from pkg.config import routes
from pkg.service.user import User
from pkg.service.user_storage import UserStorage


async def page(call: types.CallbackQuery, message: types.Message, change_user_state=True):
    reply_markup = [[{
        'text': localization.get_message(['settings', 'buttons', 'email'], message.from_user.language_code),
        'callback_data': {'tp': routes.RouteMap.type('settings_email')}}],
        [go_back_inline_button(message.from_user.language_code)]]

    message_structures = [{
        'type': 'text',
        'text': localization.get_message(['settings', 'page'], message.from_user.language_code),
        'reply_markup': reply_markup,
    }]
    await message_sender(message, resending=call is None, message_structures=message_structures)

    if change_user_state:
        UserStorage.change_page(message.chat.id, routes.RouteMap.type('settings'))


async def email(call: types.CallbackQuery, message: types.Message, change_user_state=True):
    if not is_call_or_command(call, message) and len(message.text) != 0:
        User.update_email_by_service_id(message.chat.id, message.text)

    user = User.find_by_service_id(message.chat.id)

    message_structures = [{
        'type': 'text',
        'text': localization.get_message(
            ['settings', 'email', 'page'], message.from_user.language_code,
            email=user['email'] if user['email'] is not None else localization.get_message(
                ['settings', 'email', 'empty'], message.from_user.language_code
            )),
        'reply_markup': go_back_inline_markup(message.from_user.language_code),
    }]
    await message_sender(message, resending=call is None, message_structures=message_structures)

    if is_call_or_command(call, message) and change_user_state:
        UserStorage.change_page(message.chat.id, routes.RouteMap.type('settings_email'))
