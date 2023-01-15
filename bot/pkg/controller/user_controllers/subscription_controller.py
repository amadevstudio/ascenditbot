import json

from aiogram import types

from framework.controller.message_tools import message_sender, go_back_inline_button, notify
from framework.controller import state_data
from lib.language import localization
from pkg.controller.user_controllers.common_controller import raise_error
from pkg.service.tariff import Tariff
from pkg.service.user import User
from pkg.service.user_storage import UserStorage
from pkg.template.tariff.common import build_subscription_info, channels_count_text


async def page(call: types.CallbackQuery, message: types.Message, change_user_state=True):
    user_id = User.get_id_by_service_id(message.chat.id)

    tariff_message = localization.get_message(['subscription', 'show', 'text'], message.from_user.language_code)

    user_tariff_info = Tariff.user_tariff_info(user_id)
    tariff_message += build_subscription_info(user_tariff_info, message.from_user.language_code)

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
        if tariff['id'] != 0:
            tariff_info = localization.get_message(
                ['tariffs', 'list', tariff['id']], message.from_user.language_code) + "\n"
            tariff_info += f"{float(tariff['price']) / 100} {tariff['currency_code']}\n"
            tariff_info += channels_count_text(tariff['channels_count'], message.from_user.language_code)
            tariffs_message += tariff_info + "\n\n"

        tariff_button_text = localization.get_message(
            ['tariffs', 'list', tariff['id']], message.from_user.language_code)
        if tariff['id'] == user_tariff_info['tariff_id']:
            tariff_button_text = '* ' + tariff_button_text + ' ' + localization.get_message(
                ['tariffs', 'info', 'selected'], message.from_user.language_code)
        reply_markup.add(types.InlineKeyboardButton(
            tariff_button_text, callback_data=json.dumps({'tp': 'change_tariff', 'id': tariff['id']})))

    tariffs_message += localization.get_message(['tariffs', 'current'], message.from_user.language_code) + "\n"
    tariffs_message += build_subscription_info(user_tariff_info, message.from_user.language_code)

    reply_markup.add(go_back_inline_button(message.from_user.language_code))

    await message_sender(message, message_structures=[{
        'type': 'text',
        'text': tariffs_message,
        'reply_markup': reply_markup,
        'parse_mode': 'HTML'
    }])

    if change_user_state:
        UserStorage.change_page(message.chat.id, 'tariffs')


async def change_tariff(call: types.CallbackQuery, message: types.Message):
    chosen_tariff_id = state_data.decode_call_data(call).get('id', None)

    user_id = User.get_id_by_service_id(message.chat.id)

    if user_id is None:
        await raise_error(call, message, 'user_none')
        return

    user_tariff_connection = Tariff.change(user_id, chosen_tariff_id)
    if 'error' in user_tariff_connection:
        if user_tariff_connection['error'] in ['currency_mess']:
            await raise_error(call, message, 'unexpected')
        else:
            await notify(
                call, message,
                localization.get_message(
                    ['subscription', 'errors', user_tariff_connection['error']], message.from_user.language_code),
                alert=True)
        return

    await notify(call, message, localization.get_message(['subscription', 'updated'], message.from_user.language_code))
    await tariffs(call, message, change_user_state=False)
