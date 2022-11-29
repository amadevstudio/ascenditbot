import json

from aiogram import types

from lib.language import localization
from framework.controller.message_tools import message_sender, go_back_inline_markup, call_or_command, \
    image_link_or_object, notify, go_back_inline_button
from pkg.service import user_storage, chat


async def add_chat(call: types.CallbackQuery, message: types.Message, change_user_state=True):
    if call_or_command(call, message):
        message_structures = [{
            'type': 'image',
            'image': image_link_or_object(
                localization.get_link(["add_chat", "anon_admin_example"], message.from_user.language_code)),
            'text': localization.get_message(["add_chat", "instruction"], message.from_user.language_code),
            'reply_markup': go_back_inline_markup(message.from_user.language_code)
        }]
        await message_sender(message, resending=call is None, message_structures=message_structures)

        if change_user_state:
            user_storage.change_page(message.chat.id, 'add_chat')

        return

    # Chat adding

    if message.forward_from_chat is not None:
        chat_service_id = message.forward_from_chat.id
    else:
        chat_service_id = message.text

    result_connection = await chat.add(message.bot, chat_service_id, message.from_user.id)

    if "error" in result_connection:
        if result_connection["error"] == "connection_exists":
            result_connection = result_connection["connection"]

        else:
            await notify(call, message, localization.get_message(
                    ["add_chat", "errors", result_connection["error"]], message.from_user.language_code),
                alert=True, button_text="cancel")
            return

    chat_info = await chat.get_info(message.bot, chat_service_id=str(chat_service_id))

    button = types.InlineKeyboardButton(
        localization.get_message(["buttons", "go_to_settings"], message.from_user.language_code),
        callback_data=json.dumps({'tp': 'chat', 'id': result_connection['moderated_chat_id']}))
    reply_markup = types.InlineKeyboardMarkup().add(button).add()
    reply_markup.add(go_back_inline_button(message.from_user.language_code))

    message_structures = [{
        'type': 'text',
        'text': localization.get_message(
            ["add_chat", "success"], message.from_user.language_code).format(chat_name=chat_info['title']),
        'reply_markup': reply_markup
    }]

    await message_sender(message, resending=call is None, message_structures=message_structures)
