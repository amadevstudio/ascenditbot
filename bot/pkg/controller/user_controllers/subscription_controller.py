import json

from aiogram import types

from framework.controller.message_tools import message_sender, go_back_inline_button
from lib.language import localization
from pkg.controller.user_controllers.common_controller import raise_user_none
from pkg.service.tariff import Tariff
from pkg.service.user import User
from pkg.service.user_storage import UserStorage


async def page(call: types.CallbackQuery, message: types.Message, change_user_state=True):
    user_id = User.get_id_by_service_id(message.chat.id)
    if user_id is None:
        await raise_user_none(call, message)
        return

    tariff_message = localization.get_message(['subscription', 'show', 'text'], message.from_user.language_code)

    user_tariff_info = Tariff.user_tariff_info(user_id)
    tariff_message += Tariff.build_tariff_info_message(user_tariff_info, message.from_user.language_code)

    reply_markup = types.InlineKeyboardMarkup()
    choose_tariff_button = types.InlineKeyboardButton(
        localization.get_message(['subscription', 'buttons', 'choose_tariff'], message.from_user.language_code),
        callback_data=json.dumps({'tp': 'choose_tariff'})
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
