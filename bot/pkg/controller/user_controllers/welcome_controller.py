import json

from aiogram import types

from pkg.config import routes
from pkg.template.tariff.common import build_subscription_info_short
from lib.language import localization
from framework.controller.message_tools import message_sender, go_back_inline_markup
from pkg.service.tariff import Tariff

from pkg.service.user import User
from pkg.service.user_storage import UserStorage


async def start(call: types.CallbackQuery, message: types.Message, change_user_state=True):
    if call is None:
        await message.reply('👋')
        User.register(message.chat.id, message.from_user.language_code)

    button = types.InlineKeyboardButton(localization.get_message(
        ['welcome', 'lets_begin'], message.from_user.language_code), callback_data=json.dumps({'tp': 'menu'}))
    markup = types.InlineKeyboardMarkup().add(button)

    message_structures = [{
        'type': 'text',
        'text': localization.get_message(['welcome', 'introduction'], message.from_user.language_code),
        'reply_markup': markup,
    }]
    await message_sender(message, resending=call is None, message_structures=message_structures)

    if change_user_state:
        UserStorage.new_navigation_journey(message.chat.id, 'start')


async def menu(call: types.CallbackQuery, message: types.Message, change_user_state=True):
    buttons = []
    for button_type in ['add_chat', 'my_chats', 'help', 'subscription']:
        buttons.append(types.InlineKeyboardButton(
            localization.get_message(['buttons', button_type], message.from_user.language_code),
            callback_data=json.dumps({'tp': button_type})))
    markup = types.InlineKeyboardMarkup().row(buttons[0], buttons[1])
    markup.row(buttons[2], buttons[3])

    answer_messages = []

    user_id = User.get_id_by_service_id(message.chat.id)

    trial_info = Tariff.activate_trial(user_id)
    if trial_info is not None:
        answer_messages.append({
            'type': 'text',
            'text': localization.get_message(['subscription', 'free_trial'], message.from_user.language_code),
            'parse_mode': 'Markdowns'
        })

    user_tariff_info = Tariff.user_tariff_info(user_id)
    answer_messages.append({
        'type': 'text',
        'text':
            build_subscription_info_short(user_tariff_info, message.from_user.language_code)
            + "\n\n" + localization.get_message(['menu', 'text'], message.from_user.language_code),
        'reply_markup': markup,
        'parse_mode': 'Markdown'
    })

    await message_sender(message, resending=call is None, message_structures=answer_messages)

    if change_user_state:
        UserStorage.new_navigation_journey(message.chat.id, 'menu')


async def help_page(call: types.CallbackQuery, message: types.Message, change_user_state=True):
    await message_sender(message, resending=call is None, message_structures=[{
        'type': 'text',
        'text': localization.get_message(['help', 'text'], message.from_user.language_code),
        'reply_markup': go_back_inline_markup(message.from_user.language_code)
    }])

    if change_user_state:
        UserStorage.change_page(message.chat.id, routes.RouteMap.type('help'))
