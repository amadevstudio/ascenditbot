import json

from framework.system import telegram_types

from pkg.config import routes
from pkg.template.tariff.common import build_subscription_info_short
from lib.language import localization
from framework.controller.message_tools import message_sender, go_back_inline_markup, chat_id_sender
from pkg.service.tariff import Tariff

from pkg.service.user import User
from pkg.service.user_storage import UserStorage
from project.types import UserInterface


async def start(call: telegram_types.CallbackQuery, message: telegram_types.Message, change_user_state=True):
    registration_result = None

    if call is None:
        await message.reply('👋')
        initial_data = User.analyze_initial_data(message.text)
        registration_result = User.register(message.chat.id, message.from_user.language_code, initial_data)

    markup = [[{
        'text': localization.get_message(['welcome', 'lets_begin'], message.from_user.language_code),
        'callback_data': {'tp': 'menu'}}]]

    message_structures = [{
        'type': 'text',
        'text': localization.get_message(['welcome', 'introduction'], message.from_user.language_code),
        'reply_markup': markup,
    }]
    await message_sender(
        message, resending=call is None,
        message_structures=message_structures)

    if change_user_state:
        UserStorage.new_navigation_journey(message.chat.id, routes.RouteMap.type('start'))

    if registration_result is not None and registration_result.get('refer', None) is not None:
        refer: UserInterface = registration_result['refer']
        await chat_id_sender(message.bot, int(refer['service_id']), [{
            'type': 'text',
            'text': localization.get_message(
                ['subscription', 'fund', 'from_referral', 'initialed'], refer['language_code']),
        }])


async def menu(call: telegram_types.CallbackQuery, message: telegram_types.Message, change_user_state=True):
    buttons = []
    for button_type in ['add_chat', 'my_chats', 'help', 'subscription', 'settings']:
        buttons.append({
            'text': localization.get_message(['buttons', button_type], message.from_user.language_code),
            'callback_data': {'tp': button_type}})
    markup = [[buttons[0], buttons[1]], [buttons[2], buttons[3]], [buttons[4]]]

    answer_messages = []

    user_id = User.get_id_by_service_id(message.chat.id)

    user_tariff_info = Tariff.user_tariff_info(user_id)

    trial_info = Tariff.activate_trial(user_tariff_info)
    if trial_info is not None:
        answer_messages.append({
            'type': 'text',
            'text': localization.get_message(['subscription', 'free_trial'], message.from_user.language_code),
            'parse_mode': 'HTML'
        })
        user_tariff_info = Tariff.user_tariff_info(user_id)

    answer_messages.append({
        'type': 'text',
        'text':
            build_subscription_info_short(user_tariff_info, message.from_user.language_code)
            + "\n\n" + localization.get_message(['menu', 'text'], message.from_user.language_code),
        'reply_markup': markup,
        'parse_mode': 'HTML'
    })

    await message_sender(
        message, resending=call is None, message_structures=answer_messages)

    if change_user_state:
        UserStorage.new_navigation_journey(message.chat.id, routes.RouteMap.type('menu'))


async def help_page(call: telegram_types.CallbackQuery, message: telegram_types.Message, change_user_state=True):
    await message_sender(message, resending=call is None, message_structures=[{
        'type': 'text',
        'text': localization.get_message(['help', 'text'], message.from_user.language_code),
        'reply_markup': go_back_inline_markup(message.from_user.language_code)
    }])

    if change_user_state:
        UserStorage.change_page(message.chat.id, routes.RouteMap.type('help'))
