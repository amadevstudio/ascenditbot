import json

from aiogram import types

from framework.controller.message_tools import notify, message_sender, call_or_command, go_back_inline_markup
from framework.controller.state_data import get_current_state_data
from lib.language import localization
from lib.telegram.aiogram.navigation_builder import NavigationBuilder
from pkg.config import routes
from pkg.controller.chats_controller import _PER_PAGE
from pkg.service.allowed_user import AllowedUser
from pkg.service.chat import Chat
from pkg.service.user import User
from pkg.service.user_storage import UserStorage


async def add_to_chat_whitelist(call: types.CallbackQuery, message: types.Message, change_user_state=True):
    if call_or_command(call, message):
        message_structures = [{
            'type': 'text',
            'text': localization.get_message(['chat', 'add_to_whitelist', 'text'], message.from_user.language_code),
            'reply_markup': go_back_inline_markup(message.from_user.language_code),
            'parse_mode': 'Markdown'
        }]
        await message_sender(message, resending=call is None, message_structures=message_structures)

        if change_user_state:
            UserStorage.change_page(message.chat.id, 'add_to_chat_whitelist')

        return

    # ---
    # User adding

    user_nickname = message.text

    chat_state_data = UserStorage.get_user_state_data(message.chat.id, 'chat')

    result_connection = Chat.add_to_whitelist(chat_state_data['id'], user_nickname)

    if 'error' in result_connection:
        if result_connection['error'] == 'unexpected':
            error_trace = ['errors', result_connection['error']]
        else:
            error_trace = ['chat', 'add_to_whitelist', 'errors', result_connection['error']]
        await notify(
            call, message, localization.get_message(error_trace, message.from_user.language_code),
            alert=True, button_text='cancel')
        return

    message_structures = [{
        'type': 'text',
        'text': localization.get_message(
            ['chat', 'add_to_whitelist', 'success'], message.from_user.language_code).format(nickname=user_nickname),
        'reply_markup': go_back_inline_markup(message.from_user.language_code)
    }]

    await message_sender(message, resending=call is None, message_structures=message_structures)


async def chat_whitelist(call: types.CallbackQuery, message: types.Message, change_user_state=True):
    current_type = routes.RouteMap.type('chat_whitelist')

    # Getting data and full navigation setup
    channel_state_data = UserStorage.get_user_state_data(message.chat.id, routes.RouteMap.type('chat'))
    state_data = UserStorage.get_user_state_data(message.chat.id, current_type)

    current_page, chat_whitelist_page_data, routing_helper_message, nav_layout = NavigationBuilder().full_message_setup(
        call, message, state_data, current_type, message.from_user.language_code,

        Chat.whitelist_data_provider, [channel_state_data['id']],
        Chat.whitelist_data_count_provider, [channel_state_data['id']],
        _PER_PAGE, 'created_at'
    )

    # Error processing
    if 'error' in chat_whitelist_page_data:
        if chat_whitelist_page_data['error'] in ['empty']:
            error_message = localization.get_message(
                ['chat_whitelist', 'errors', chat_whitelist_page_data['error']],
                message.from_user.language_code,
                command=routes.RouteMap.get_route_main_command('add_chat'))
        else:
            error_message = localization.get_message(
                ['navigation_builder', 'errors', chat_whitelist_page_data['error']],
                message.from_user.language_code)
        await notify(
            call, message, error_message, alert=True)
        return

    # Building message
    message_text = localization.get_message(['chat_whitelist', 'list', 'main'], message.from_user.language_code)
    message_text += '\n' + routing_helper_message

    # Chat buttons
    reply_markup = types.InlineKeyboardMarkup()
    for whitelist_data in chat_whitelist_page_data['data']:
        button_text = localization.get_message(
            ['whitelist', 'list', 'button', 'active' if whitelist_data['active'] else 'inactive'],
            message.from_user.language_code, nickname=whitelist_data['nickname'])

        b = types.InlineKeyboardButton(
            text=button_text,
            callback_data=json.dumps({'tp': 'chat_whitelist_member', 'id': whitelist_data['id']}))
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
        UserStorage.add_user_state_data(message.chat.id, current_type, {'p': current_page})


async def allowed_user(call: types.CallbackQuery, message: types.message, change_user_state=True):
    allowed_user_state_data = get_current_state_data(call, message, 'allowed_user')
    chat_state_data = UserStorage.get_user_state_data(message.chat.id, 'chat')

    if not len(allowed_user_state_data) or not len(chat_state_data):
        await notify(
            None, message, localization.get_message(['errors', 'state_data_none'], message.from_user.language_code))
        return

    user_data = AllowedUser.find(allowed_user_state_data['id'])
    if user_data is None:
        await notify(
            call, message, localization.get_message(['chat', 'errors', 'not_found'], message.from_user.language_code))
        return

    chat_info = await Chat.load_info(call.bot, str(chat_state_data['service_id']))

    message_text = localization.get_message(
        ['allowed_user', 'show', 'text'], message.from_user.language_code, chat_name=chat_info['title'])

    reply_markup = types.InlineKeyboardMarkup()
    add_to_whitelist_button = types.InlineKeyboardButton(
        localization.get_message(['chat', 'show', 'add_to_whitelist_button'], message.from_user.language_code),
        callback_data=json.dumps({'tp': 'add_to_chat_whitelist'})
    )
    reply_markup.add(add_to_whitelist_button)
    whitelist_button = types.InlineKeyboardButton(
        localization.get_message(['chat', 'show', 'whitelist_button'], message.from_user.language_code),
        callback_data=json.dumps({'tp': 'chat_whitelist'})
    )
    reply_markup.add(whitelist_button)
    state_button = types.InlineKeyboardButton(
        localization.get_message(
            ['chat', 'show', 'active_button', 'active' if user_data['active'] else 'inactive'],
            message.from_user.language_code,
        ), callback_data=json.dumps({'tp': 'switch_active'}))
    reply_markup.add(state_button)
    reply_markup.add(go_back_inline_button(message.from_user.language_code))

    message_structures = [{
        'type': 'text',
        'text': message_text,
        'reply_markup': reply_markup
    }]
    await message_sender(message, message_structures=message_structures)

    if change_user_state:
        UserStorage.change_page(message.chat.id, 'chat')
        UserStorage.add_user_state_data(message.chat.id, 'chat', user_data)
