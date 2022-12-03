import json

from aiogram import types

from lib.language import localization
from framework.controller.message_tools import message_sender, go_back_inline_markup, call_or_command, \
    image_link_or_object, notify, go_back_inline_button
from lib.telegram.aiogram.navigation_builder import NavigationBuilder
from pkg.config import routes
from pkg.service.user_storage import UserStorage
from pkg.service.chat import Chat

_PER_PAGE = 5


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
            UserStorage.change_page(message.chat.id, 'add_chat')

        return

    # Chat adding

    if message.forward_from_chat is not None:
        chat_service_id = message.forward_from_chat.id
    else:
        chat_service_id = message.text

    result_connection = await Chat.add(message.bot, chat_service_id, message.from_user.id)

    if "error" in result_connection:
        if result_connection["error"] == "connection_exists":
            result_connection = result_connection["connection"]

        else:
            await notify(call, message, localization.get_message(
                ["add_chat", "errors", result_connection["error"]], message.from_user.language_code),
                         alert=True, button_text="cancel")
            return

    chat_info = await Chat.get_info(message.bot, chat_service_id=str(chat_service_id))

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


async def my_chats(call: types.CallbackQuery, message: types.Message, change_user_state=True):
    current_type = routes.RouteMap.type("my_chats")

    # Getting data and full navigation setup
    state_data = UserStorage.get_user_state_data(message.chat.id, current_type)
    current_page, user_chat_page_data, routing_helper_message, nav_layout = NavigationBuilder().full_message_setup(
        call, message, state_data, current_type, message.from_user.language_code,

        Chat.data_provider_by_service_id, [message.chat.id],
        Chat.data_count_provider_by_service_id, [message.chat.id],
        _PER_PAGE, "created_at"
    )

    # Error processing
    if "error" in user_chat_page_data:
        if user_chat_page_data["error"] in ["empty"]:
            error_message = localization.get_message(
                ["my_chats", "errors", user_chat_page_data["error"]],
                message.from_user.language_code,
                command=routes.RouteMap.get_route_main_command("add_chat"))
        else:
            error_message = localization.get_message(
                ["navigation_builder", "errors", user_chat_page_data["error"]],
                message.from_user.language_code)
        await notify(
            call, message, error_message, alert=True)
        return

    # Building message
    message_text = localization.get_message(["my_chats", "list", "main"], message.from_user.language_code)
    message_text += "\n" + routing_helper_message

    # Chat buttons
    reply_markup = types.InlineKeyboardMarkup()
    for chat_data in user_chat_page_data["data"]:
        chat_info = await Chat.get_info(message.bot, chat_service_id=str(chat_data['service_id']))

        button_text = localization.get_message(
            ["my_chats", "list", "chat_button", "active" if chat_data['active'] else "inactive"],
            message.from_user.language_code, chat_name=chat_info["title"])

        button_data = {"tp": "chat", "id": chat_data['id']}

        b = types.InlineKeyboardButton(
            text=button_text,
            callback_data=json.dumps(button_data))
        reply_markup.add(b)

    # Navigation markup
    reply_markup.add(*nav_layout)

    # Sending
    message_structures = [{
        'type': 'text',
        'text': message_text,
        'reply_markup': reply_markup
    }]
    await message_sender(message, resending=call is None, message_structures=message_structures)

    if change_user_state:
        UserStorage.change_page(message.chat.id, current_type)


async def show(call: types.CallbackQuery, message: types.Message, change_user_state=True):
    chat_button_data = json.loads(call.data)
    chat_data = Chat.find(chat_button_data['id'])
    if chat_data is None:
        await notify(
            call, message, localization.get_message(['chat', 'errors', 'not_found'], message.from_user.language_code))
        return

    chat_info = await Chat.get_info(call.bot, str(chat_data['service_id']))

    message_text = localization.get_message(
        ['chat', 'show', 'text'], message.from_user.language_code, chat_name=chat_info['title'])

    reply_markup = types.InlineKeyboardMarkup()
    whitelist_button = types.InlineKeyboardButton(
        localization.get_message(['chat', 'show', 'whitelist_button'], message.from_user.language_code),
        callback_data=json.dumps({'type': 'chat_whitelist'})
    )
    reply_markup.add(whitelist_button)
    state_button = types.InlineKeyboardButton(
        localization.get_message(
            ['chat', 'show', 'active_button', 'active' if chat_data['active'] else 'inactive'],
            message.from_user.language_code,
        ), callback_data=json.dumps({'type': 'chat_state'}))
    reply_markup.add(state_button)
    reply_markup.add(go_back_inline_button(message.from_user.language_code))

    message_structures = [{
        'type': 'text',
        'text': message_text,
        'reply_markup': reply_markup
    }]
    await message_sender(message, message_structures=message_structures)

    if change_user_state:
        UserStorage.change_page(message.chat.id, "my_chat")
