import json

from aiogram import types

from framework.controller.message_tools import message_sender, go_back_inline_button
from lib.language import localization
from pkg.service.tariff import Tariff
from pkg.service.user import User
from pkg.service.user_storage import UserStorage


async def page(call: types.CallbackQuery, message: types.Message, change_user_state=True):
    user_id = User.get_id_by_service_id(message.chat.id)

    tariff_message = localization.get_message(['subscription', 'show', 'text'], message.from_user.language_code)

    user_tariff_info = Tariff.user_tariff_info(user_id)
    tariff_message += Tariff.build_subscription_info(user_tariff_info, message.from_user.language_code)

    reply_markup = types.InlineKeyboardMarkup()
    choose_tariff_button = types.InlineKeyboardButton(
        localization.get_message(['subscription', 'buttons', 'choose_tariff'], message.from_user.language_code),
        callback_data=json.dumps({'tp': 'tariffs'})
    )
    reply_markup.add(choose_tariff_button)
    replenish_button = types.InlineKeyboardButton(
        localization.get_message(['subscription', 'buttons', 'replenish'], message.from_user.language_code),
        callback_data=json.dumps({'tp': 'replenish'})
    )
    reply_markup.add(replenish_button)
    reply_markup.add(go_back_inline_button(message.from_user.language_code))

    message_structures = [{
        'type': 'text',
        'text': tariff_message,
        'reply_markup': reply_markup,
        'parse_mode': 'HTML'
    }]
    await message_sender(message, resending=call is None, message_structures=message_structures)
    if change_user_state:
        UserStorage.change_page(message.chat.id, 'subscription')


async def tariffs(_, message: types.Message, change_user_state=True):
    user_id = User.get_id_by_service_id(message.chat.id)
    user_tariff_info = Tariff.user_tariff_info(user_id)

    available_tariffs = Tariff.tariffs_info(user_id)

    tariffs_message = localization.get_message(['tariffs', 'index'], message.from_user.language_code)
    reply_markup = types.InlineKeyboardMarkup()

    for tariff in available_tariffs:
        tariff_info = localization.get_message(
            ['tariffs', 'list', tariff['id']], message.from_user.language_code) + "\n"
        tariff_info += f"{float(tariff['price']) / 100} {tariff['currency_code']}\n"
        tariff_info += Tariff.channels_count_text(tariff['channels_count'], message.from_user.language_code)
        tariffs_message += tariff_info + "\n\n"

        tariff_button_text = localization.get_message(
            ['tariffs', 'list', tariff['id']], message.from_user.language_code)
        if tariff['id'] == user_tariff_info['tariff_id']:
            tariff_button_text = '* ' + tariff_button_text + ' ' + localization.get_message(
                ['tariffs', 'info', 'selected'], message.from_user.language_code)
        reply_markup.add(types.InlineKeyboardButton(
            tariff_button_text, callback_data=json.dumps({'tp': 'tariff', 'id': tariff['id']})))

    tariffs_message += localization.get_message(['tariffs', 'current'], message.from_user.language_code) + "\n"
    tariffs_message += Tariff.build_subscription_info(user_tariff_info, message.from_user.language_code)

    no_subscription_button_text = localization.get_message(['tariffs', 'disable'], message.from_user.language_code)
    if user_tariff_info['tariff_id'] == 0:
        no_subscription_button_text = '* ' + no_subscription_button_text \
            + f" {localization.get_message(['tariffs', 'info', 'selected'], message.from_user.language_code)}"
    reply_markup.add(types.InlineKeyboardButton(
        no_subscription_button_text, callback_data=json.dumps({'tp': 'tariff', 'id': 0})))

    reply_markup.add(go_back_inline_button(message.from_user.language_code))

    await message_sender(message, message_structures=[{
        'type': 'text',
        'text': tariffs_message,
        'reply_markup': reply_markup,
        'parse_mode': 'HTML'
    }])

    if change_user_state:
        UserStorage.change_page(message.chat.id, 'tariffs')
