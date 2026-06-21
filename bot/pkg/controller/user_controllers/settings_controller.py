from framework.controller.types import ControllerParams

from framework.controller.message_tools import message_sender, go_back_inline_markup, go_back_inline_button, \
    is_call_or_command
from lib.language import localization
from pkg.config import routes
from pkg.service.tariff import Tariff
from pkg.service.user import User


async def page(params: ControllerParams):
    call, message = params['call'], params['message']

    reply_markup = [[{
        'text': localization.get_message(['settings', 'buttons', 'email'], params['language_code']),
        'callback_data': {'tp': routes.RouteMap.type('settings_email')}}],
        [{
            'text': localization.get_message(['settings', 'buttons', 'currency'], params['language_code']),
            'callback_data': {'tp': routes.RouteMap.type('settings_currency')}}],
        [go_back_inline_button(params['language_code'])]]

    message_structures = [{
        'type': 'text',
        'text': localization.get_message(['settings', 'page'], params['language_code']),
        'reply_markup': reply_markup,
    }]
    await message_sender(message.chat.id, message_structures=message_structures)


async def email(params: ControllerParams):
    call, message = params['call'], params['message']

    if not is_call_or_command(call, message) and len(message.text) != 0:
        await User.update_email_by_service_id(message.chat.id, message.text)

    user = await User.find_by_service_id(message.chat.id)

    message_structures = [{
        'type': 'text',
        'text': localization.get_message(
            ['settings', 'email', 'page'], params['language_code'],
            email=user['email'] if user['email'] is not None else localization.get_message(
                ['settings', 'email', 'empty'], params['language_code']
            )),
        'reply_markup': go_back_inline_markup(params['language_code']),
    }]
    await message_sender(message.chat.id, message_structures=message_structures)


async def currency(params: ControllerParams):
    call, message = params['call'], params['message']

    user_id = await User.get_id_by_service_id(message.chat.id)
    user_tariff_info = await Tariff.user_tariff_info(user_id)

    reply_markup = []
    for currency_item in await Tariff.enabled_currencies():
        button_text = currency_item['title']
        if currency_item['code'] == user_tariff_info['currency_code']:
            button_text = '* ' + button_text

        reply_markup.append([{
            'text': button_text,
            'callback_data': {'tp': 'change_currency', 'currency': currency_item['code']}
        }])

    reply_markup.append([go_back_inline_button(params['language_code'])])

    await message_sender(message.chat.id, message_structures=[{
        'type': 'text',
        'text': localization.get_message(
            ['settings', 'currency', 'page'], params['language_code'],
            currency=user_tariff_info['currency_code']),
        'reply_markup': reply_markup
    }])


async def change_currency(params: ControllerParams):
    call, message, current_state_data = params['call'], params['message'], params['state_data']

    currency_code = current_state_data.get('currency', None)
    user_id = await User.get_id_by_service_id(message.chat.id)
    if currency_code is not None:
        await Tariff.set_payment_currency(user_id, currency_code)

    await currency(params)
