import copy
import json
import time
from typing import Literal, TypedDict, Any

import aiogram
from aiogram import types

from lib.language import localization
from lib.telegram.aiogram.message_master import message_master, get_timeout_from_error_bot, MasterMessages, \
    MessageStructuresInterface, ButtonData
from lib.telegram.aiogram.message_processor import call_and_message_accessed_processor
from pkg import config
from pkg.controller.bot_setup import bot
from pkg.service.user_storage import UserStorage
from pkg.system.logger import logger


def go_back_inline_markup(language_code: str, button_text: Literal['back', 'cancel'] = 'back') \
        -> list[list[ButtonData]]:
    return[[go_back_inline_button(language_code, button_text)]]


def go_back_inline_button(language_code: str, button_text: Literal['back', 'cancel'] = 'back') -> ButtonData:
    return {'text': localization.get_message(["buttons", button_text], language_code), 'callback_data': {'tp': 'back'}}


def image_link_or_object(path: str):
    if path[0:2] == "./":
        return types.FSInputFile(path)

    return path


async def chat_id_sender(
        bot: aiogram.Bot, user_chat_id: int, message_structures: list[MessageStructuresInterface] = None):
    for message_to_send in message_structures:
        message_structure = message_to_send

        if message_structure['type'] == MasterMessages.text.value:
            result = await bot.send_message(
                chat_id=user_chat_id,
                text=message_structure.get('text', None),
                parse_mode=message_structure.get('parse_mode', None),
                reply_markup=message_structure.get('reply_markup', None),
                disable_web_page_preview=message_structure.get('disable_web_page_preview', None))

        elif message_structure['type'] == MasterMessages.image.value:
            result = await bot.send_photo(
                chat_id=user_chat_id,
                photo=message_structure.get('image', None),
                caption=message_structure.get('text', None),
                parse_mode=message_structure.get('parse_mode', None),
                reply_markup=message_structure.get('reply_markup', None))

    UserStorage.set_resend(user_chat_id)


async def message_sender(
        message: types.Message, resending=False,
        message_structures: list[MessageStructuresInterface] = None):

    if message_structures is None:
        message_structures = []

    resending |= UserStorage.should_resend(message.chat.id)

    previous_message_structures = UserStorage.get_message_structures(message.chat.id) if resending is False else []

    new_message_structures = None
    try:
        new_message_structures = await message_master(
            bot, message, resending=resending, message_structures=message_structures,
            previous_message_structures=previous_message_structures)
    except aiogram.exceptions.TelegramBadRequest:  # except utils.exceptions.MessageNotModified:
        pass
    except Exception as e:
        timeout = get_timeout_from_error_bot(e)
        if timeout:
            time.sleep(timeout)
            new_message_structures = await message_master(
                bot, message, resending=resending, message_structures=message_structures,
                previous_message_structures=previous_message_structures)
        else:
            logger.err(e)

        # bot_blocked_reaction(e, chat_id)

    if new_message_structures is not None:
        UserStorage.set_message_structures(message.chat.id, new_message_structures)

    UserStorage.set_resend(message.chat.id, False)


async def notify(
        call: types.CallbackQuery | None, message: types.Message, text: str,
        alert: bool = False, button_text: Literal['back', 'cancel'] = 'back'
):
    if call is not None:
        await bot.answer_callback_query(
            callback_query_id=call.id, show_alert=alert, text=text)
        return

    message_structures = [{
        'type': 'text',
        'text': text,
        'reply_markup': go_back_inline_markup(message.from_user.language_code, button_text=button_text)
    }]
    await message_sender(message, resending=True, message_structures=message_structures)
    UserStorage.change_page(message.chat.id, config.routes.RouteMap.type('nowhere'))


def is_command(message_text: str) -> bool:
    return message_text and message_text.startswith('/')


def is_call_or_command(call: types.CallbackQuery = None, message: types.Message = None,
                       entity: types.Message | types.CallbackQuery = None) -> bool:
    """
    If entity passed call and message are ignored
    """
    if entity is not None:
        call, message = call_and_message_accessed_processor(entity)

    return call is not None or (call is None and message.text is not None and message.text[0]) == '/'


def determine_search_query(
        call: types.CallbackQuery | None, message: types.Message, state_data: dict[str, Any]) -> dict[str, Any]:
    local_state_data = copy.deepcopy(state_data)

    if call is None and message.text != '':
        try:
            int(message.text)
        except ValueError:
            local_state_data['search_query'] = message.text
            return local_state_data

    if 'search_query' in local_state_data and local_state_data['search_query'] is None:
        del local_state_data['search_query']

    return local_state_data
