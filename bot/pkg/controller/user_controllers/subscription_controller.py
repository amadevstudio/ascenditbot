import json

from aiogram import types

from framework.controller.message_tools import message_sender, go_back_inline_button, notify, go_back_inline_markup
from framework.controller import state_data
from lib.language import localization
from lib.payment.services.robokassa import RobokassaPaymentProcessor
from pkg.controller.user_controllers.common_controller import raise_error
from pkg.service.payment import Payment
from pkg.service.tariff import Tariff
from pkg.service.user import User
from pkg.service.user_storage import UserStorage
from pkg.system.logger import logger
from pkg.template.tariff.common import build_subscription_info, channels_count_text
from project import constants


async def page(call: types.CallbackQuery, message: types.Message, change_user_state=True):
    user_id = User.get_id_by_service_id(message.chat.id)

    tariff_message = localization.get_message(['subscription', 'show', 'text'], message.from_user.language_code)
    tariff_message += "\n\n" + localization.get_message(
        ['subscription', 'show', 'balance_warning'], message.from_user.language_code)
    tariff_message += "\n\n" + localization.get_message(['tariffs', 'current'], message.from_user.language_code)

    user_tariff_info = Tariff.user_tariff_info(user_id)
    tariff_message += "\n\n" + build_subscription_info(user_tariff_info, message.from_user.language_code)

    reply_markup = types.InlineKeyboardMarkup()
    choose_tariff_button = types.InlineKeyboardButton(
        localization.get_message(['subscription', 'buttons', 'choose_tariff'], message.from_user.language_code),
        callback_data=json.dumps({'tp': 'tariffs'})
    )
    reply_markup.add(choose_tariff_button)
    replenish_button = types.InlineKeyboardButton(
        localization.get_message(['subscription', 'buttons', 'fund'], message.from_user.language_code),
        callback_data=json.dumps({'tp': 'fund'})
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

    tariffs_message += "\n\n" + localization.get_message(
        ['subscription', 'show', 'balance_warning'], message.from_user.language_code)

    for tariff in available_tariffs:
        if tariff['id'] != 0:
            tariff_info = localization.get_message(
                ['tariffs', 'list', tariff['id']], message.from_user.language_code) + ", "

            per_days_message = f"/ {constants.tariff_duration_days} " + localization.get_numerical_declension_message(
                ['subscription', 'info_block', 'days_countable'], message.from_user.language_code,
                constants.tariff_duration_days)

            tariff_info += f"{Tariff.user_amount(tariff['price'])} {tariff['currency_code']} {per_days_message}, "
            tariff_info += channels_count_text(tariff['channels_count'], message.from_user.language_code).lower()
            tariffs_message += "\n\n" + tariff_info

        tariff_button_text = localization.get_message(
            ['tariffs', 'list', tariff['id']], message.from_user.language_code)
        if tariff['id'] == user_tariff_info['tariff_id']:
            tariff_button_text = '* ' + tariff_button_text + ' ' + localization.get_message(
                ['tariffs', 'info', 'selected'], message.from_user.language_code)
        reply_markup.add(types.InlineKeyboardButton(
            tariff_button_text, callback_data=json.dumps({'tp': 'change_tariff', 'id': tariff['id']})))

    tariffs_message += "\n\n" + localization.get_message(['tariffs', 'current'], message.from_user.language_code)
    tariffs_message += "\n" + build_subscription_info(user_tariff_info, message.from_user.language_code)

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


async def fund_balance_page(call: types.CallbackQuery, message: types.Message, change_user_state=True):
    user_id = User.get_id_by_service_id(message.chat.id)

    user_currency_code = Tariff.currency_code_for_user(user_id)
    available_tariffs = Tariff.tariffs_info(user_id)

    message_text = localization.get_message(
        ['subscription', 'fund', 'page'], message.from_user.language_code, user_currency_code=user_currency_code)

    reply_markup = types.InlineKeyboardMarkup()
    reply_markup_row_buffer = []

    for tariff in available_tariffs:
        if tariff['price'] == 0:
            continue

        reply_markup_row_buffer.append(types.InlineKeyboardButton(
            f"{Tariff.user_amount(tariff['price'])} {user_currency_code}",
            callback_data=json.dumps({
                'tp': 'fund_amount', 'value': Tariff.user_amount(tariff['price'])  # , 'currency': user_currency_code
            })))

        if len(reply_markup_row_buffer) == 3:
            reply_markup.row(*reply_markup_row_buffer)
            reply_markup_row_buffer = []

    reply_markup.row(*reply_markup_row_buffer)

    reply_markup.add(go_back_inline_button(message.from_user.language_code))

    await message_sender(message, message_structures=[{
        'type': 'text',
        'text': message_text,
        'reply_markup': reply_markup
    }])

    if change_user_state:
        UserStorage.change_page(message.chat.id, 'fund')


async def fund_link_page(call: types.CallbackQuery, message: types.Message, change_user_state=True):
    fund_service = Payment.get_fund_service()

    if call is not None:
        summa = state_data.decode_call_data(call).get('value', 0)
    else:
        summa = message.text  # Payment.is_test

    try:
        amount = float(summa)
        if amount <= 0:
            raise ValueError("The amount must be greater than zero")
    except Exception:
        await notify(call, message, localization.get_message(
            ['subscription', 'fund', 'errors', 'wrong_amount'], message.from_user.language_code))
        return

    user = User.find_by_service_id(message.chat.id)
    user_currency_code = Tariff.currency_code_for_user(user['id'])

    fund_link = Payment.generate_payment_link(amount, user, user_currency_code, fund_service)
    if isinstance(fund_link, dict) and 'error' in fund_link:
        await notify(call, message, localization.get_message(
            ['subscription', 'fund', 'errors', 'wrong_currency'], message.from_user.language_code))
        logger.warn(f"Wrong currency for user with id #{user['id']}, #{user_currency_code}")
        return

    message_text = localization.get_message(
            ['subscription', 'fund', 'fund_link_message'], message.from_user.language_code, link=fund_link)

    await message_sender(message, message_structures=[{
        'type': 'text',
        'text': message_text,
        'reply_markup': go_back_inline_markup(message.from_user.language_code)
    }], resending=call is None)

    if change_user_state:
        UserStorage.change_page(message.chat.id, 'fund_amount')
