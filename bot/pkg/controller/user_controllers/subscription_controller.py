from framework.controller import state_data
from framework.controller.message_tools import message_sender, go_back_inline_button, notify, go_back_inline_markup
from framework.controller.types import ControllerParams
from lib.language import localization
from pkg.controller.user_controllers.common_controller import raise_error
from pkg.service.payment import Payment
from pkg.service.tariff import Tariff
from pkg.service.user import User
from pkg.system.logger import logger
from pkg.template.tariff.common import build_subscription_info, channels_count_text
from project import constants


async def page(params: ControllerParams):
    call, message = params['call'], params['message']

    user_id = User.get_id_by_service_id(message.chat.id)

    tariff_message = localization.get_message(['subscription', 'show', 'text'], params['language_code'])
    tariff_message += "\n\n" + localization.get_message(
        ['subscription', 'show', 'balance_warning'], params['language_code'])

    referral_link = User.generate_referral_link(message.chat.id)
    tariff_message += "\n\n" + localization.get_message(
        ['subscription', 'referral'], params['language_code'], referral_link=referral_link)

    tariff_message += "\n\n" + localization.get_message(['tariffs', 'current'], params['language_code'])
    user_tariff_info = Tariff.user_tariff_info(user_id)
    tariff_message += "\n\n" + build_subscription_info(user_tariff_info, params['language_code'])

    reply_markup = []
    choose_tariff_button = {
        'text': localization.get_message(['subscription', 'buttons', 'choose_tariff'], params['language_code']),
        'callback_data': {'tp': 'tariffs'}}
    reply_markup.append([choose_tariff_button])
    replenish_button = {
        'text': localization.get_message(['subscription', 'buttons', 'fund'], params['language_code']),
        'callback_data': {'tp': 'fund'}}
    reply_markup.append([replenish_button])
    reply_markup.append([go_back_inline_button(params['language_code'])])

    message_structures = [{
        'type': 'text',
        'text': tariff_message,
        'reply_markup': reply_markup,
        'parse_mode': 'HTML',
        'disable_web_page_preview': True
    }]
    await message_sender(message, message_structures=message_structures)


async def tariffs(params: ControllerParams):
    call, message = params['call'], params['message']

    user_id = User.get_id_by_service_id(message.chat.id)
    user_tariff_info = Tariff.user_tariff_info(user_id)

    available_tariffs = Tariff.tariffs_info(user_id)

    tariffs_message = localization.get_message(['tariffs', 'index'], params['language_code'])
    reply_markup = []

    tariffs_message += "\n\n" + localization.get_message(
        ['subscription', 'show', 'balance_warning'], params['language_code'])

    for tariff in available_tariffs:
        if tariff['id'] != 0:
            tariff_info = localization.get_message(
                ['tariffs', 'list', tariff['id']], params['language_code']) + ", "

            per_days_message = f"/ {constants.tariff_duration_days} " + localization.get_numerical_declension_message(
                ['subscription', 'info_block', 'days_countable'], params['language_code'],
                constants.tariff_duration_days)

            tariff_info += f"{Tariff.user_amount(tariff['price'])} {tariff['currency_code']} {per_days_message}, "
            tariff_info += channels_count_text(tariff['channels_count'], params['language_code']).lower()
            tariffs_message += "\n\n" + tariff_info

        tariff_button_text = localization.get_message(
            ['tariffs', 'list', tariff['id']], params['language_code'])
        if tariff['id'] == user_tariff_info['tariff_id']:
            tariff_button_text = '* ' + tariff_button_text + ' ' + localization.get_message(
                ['tariffs', 'info', 'selected'], params['language_code'])
        reply_markup.append([{
            'text': tariff_button_text, 'callback_data': {'tp': 'change_tariff', 'id': tariff['id']}}])

    tariffs_message += "\n\n" + localization.get_message(['tariffs', 'current'], params['language_code'])
    tariffs_message += "\n" + build_subscription_info(user_tariff_info, params['language_code'])

    reply_markup.append([go_back_inline_button(params['language_code'])])

    await message_sender(message, message_structures=[{
        'type': 'text',
        'text': tariffs_message,
        'reply_markup': reply_markup,
        'parse_mode': 'HTML'
    }])


async def change_tariff(params: ControllerParams):
    call, message, current_state_data = params['call'], params['message'], params['state_data']

    chosen_tariff_id = current_state_data.get('id', None)

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
                    ['subscription', 'errors', user_tariff_connection['error']], params['language_code']),
                alert=True)
        return False

    await notify(call, message, localization.get_message(['subscription', 'updated'], params['language_code']))
    await tariffs(params)


async def fund_balance_page(params: ControllerParams):
    call, message = params['call'], params['message']

    user = User.find_by_service_id(message.chat.id)
    user_id = user['id']

    user_currency_code = Tariff.currency_code_for_user(user_id)
    available_tariffs = Tariff.tariffs_info(user_id)

    message_text = localization.get_message(
        ['subscription', 'fund', 'page'], params['language_code'], email=user['email'])
    message_text += "\n\n" + localization.get_message(
        ['subscription', 'show', 'balance_warning'], params['language_code'])

    reply_markup = []
    reply_markup_row_buffer = []

    for tariff in available_tariffs:
        if tariff['price'] == 0:
            continue

        reply_markup_row_buffer.append({
            'text': f"{Tariff.user_amount(tariff['price'])} {user_currency_code}",
            'callback_data': {
                'tp': 'fund_amount', 'value': Tariff.user_amount(tariff['price'])  # , 'currency': user_currency_code
            }})

        if len(reply_markup_row_buffer) == 3:
            reply_markup.append(reply_markup_row_buffer)
            reply_markup_row_buffer = []

    if len(reply_markup_row_buffer) > 0:
        reply_markup.append(reply_markup_row_buffer)

    reply_markup.append([go_back_inline_button(params['language_code'])])

    await message_sender(message, message_structures=[{
        'type': 'text',
        'text': message_text,
        'reply_markup': reply_markup,
        'parse_mode': 'HTML'
    }])


async def fund_link_page(params: ControllerParams):
    call, message = params['call'], params['message']

    fund_service = Payment.get_fund_service()

    if call is not None:
        summa = state_data.decode_call_data(call).get('value', 0)
    else:
        summa = message.text  # Payment.is_test

    try:
        amount = float(summa)  # may raise ValueError
        if amount <= 0:
            raise ValueError("The amount must be greater than zero")
    except ValueError:
        await notify(call, message, localization.get_message(
            ['subscription', 'fund', 'errors', 'wrong_amount'], params['language_code']))
        return False

    user = User.find_by_service_id(message.chat.id)
    user_currency_code = Tariff.currency_code_for_user(user['id'])

    fund_link = Payment.generate_payment_link(amount, user, user_currency_code, fund_service)
    if isinstance(fund_link, dict) and 'error' in fund_link:
        await notify(call, message, localization.get_message(
            ['subscription', 'fund', 'errors', 'wrong_currency'], params['language_code']))
        logger.warn(f"Wrong currency for user with id #{user['id']}, #{user_currency_code}")
        return False

    message_text = localization.get_message(
            ['subscription', 'fund', 'fund_link_message'], params['language_code'], link=fund_link)

    await message_sender(message, message_structures=[{
        'type': 'text',
        'text': message_text,
        'reply_markup': go_back_inline_markup(params['language_code'])
    }])
