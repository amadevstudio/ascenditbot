import json
import time

from aiogram import types, utils

from lib.language import localization
from lib.telegram.aiogram.message_master import message_master, get_timeout_from_error_bot
import pkg.config as pkg_config
from lib.telegram.aiogram.message_processor import call_and_message_accessed_processor
from pkg.service import user_storage
from pkg.system.logger import logger


def go_back_inline_markup(language_code: str, button_text: str = "back"):
    button = types.InlineKeyboardButton(localization.get_message(
        ["buttons", button_text], language_code), callback_data=json.dumps({'tp': 'back'}))
    return types.InlineKeyboardMarkup().add(button)


def image_link_or_object(path: str):
    if path[0:2] == "./":
        return types.InputFile(path)

    return path


async def message_sender(
        message: types.Message, resending=False, message_structures=[]):
    resending |= user_storage.should_resend(message.chat.id)

    previous_message_structures = user_storage.get_message_structures(message.chat.id) if resending is False else []

    new_message_structures = None
    try:
        new_message_structures = await message_master(
            message, resending=resending, message_structures=message_structures,
            previous_message_structures=previous_message_structures)
    except utils.exceptions.MessageNotModified:
        pass
    except Exception as e:
        timeout = get_timeout_from_error_bot(e)
        if timeout:
            time.sleep(timeout)
            new_message_structures = await message_master(
                message, resending=resending, message_structures=message_structures,
                previous_message_structures=previous_message_structures)
        else:
            raise e

        # bot_blocked_reaction(e, chat_id)

    if new_message_structures is not None:
        user_storage.set_message_structures(message.chat.id, new_message_structures)


async def notify(
        call: types.CallbackQuery, message: types.Message, text: str, alert: bool = False, button_text: str = "back"):
    if call is not None:
        call.bot.answer_callback_query(
            callback_query_id=call.id, show_alert=alert, text=text)
        return

    message_structures = [{
        'type': 'text',
        'text': text,
        'reply_markup': go_back_inline_markup(message.from_user.language_code, button_text=button_text)
    }]
    await message_sender(message, resending=True, message_structures=message_structures)


def call_or_command(call: types.CallbackQuery = None, message: types.Message = None,
                    entity: types.Message | types.CallbackQuery = None) -> bool:
    """
    If entity passed call and message are ignored
    """
    if entity is not None:
        call, message = call_and_message_accessed_processor(entity)

    return call is not None or message.text[0] == '/'
