import json

from framework.system import telegram_types

from framework.controller.message_tools import notify, message_sender, is_call_or_command, go_back_inline_markup, \
    go_back_inline_button, determine_search_query
from framework.controller import state_data
from lib.language import localization
from lib.telegram.aiogram.navigation_builder import NavigationBuilder
from pkg.config import routes
from pkg.controller.user_controllers.chats_controller import _PER_PAGE
from pkg.controller.user_controllers.common_controller import raise_error
from pkg.service.allowed_user import AllowedUser
from pkg.service.chat import Chat
from pkg.service.user_storage import UserStorage


# Add user to whitelist
async def add_to_chat_whitelist(call: telegram_types.CallbackQuery, message: telegram_types.Message, change_user_state=True):
    if is_call_or_command(call, message):
        message_structures = [{
            'type': 'text',
            'text': localization.get_message(['chat', 'add_to_whitelist', 'text'], message.from_user.language_code),
            'reply_markup': go_back_inline_markup(message.from_user.language_code),
            'parse_mode': 'HTML'
        }]
        await message_sender(message, resending=call is None, message_structures=message_structures)

        if change_user_state:
            UserStorage.change_page(message.chat.id, routes.RouteMap.type('add_to_chat_whitelist'))

        return

    # ---
    # User adding

    user_nickname = message.text

    # Rid of the leading @: @zxc -> zxc
    if user_nickname[0] == '@':
        user_nickname = user_nickname[1:]

    chat_state_data = state_data.get_local_state_data(message, 'chat')

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


# Show chat whitelist
async def chat_whitelist(call: telegram_types.CallbackQuery, message: telegram_types.Message, change_user_state=True):
    current_type = routes.RouteMap.type('chat_whitelist')

    # Getting data and full navigation setup
    channel_state_data = state_data.get_local_state_data(message, routes.RouteMap.type('chat'))
    whitelist_state_data = state_data.get_state_data(call, message, current_type)

    whitelist_state_data = determine_search_query(call, message, whitelist_state_data)
    search_query = whitelist_state_data.get('search_query', None)

    chat_info = await Chat.load_info(str(channel_state_data['service_id']))

    current_page, chat_whitelist_page_data, routing_helper_message, nav_layout = NavigationBuilder().full_message_setup(
        call, message, whitelist_state_data, current_type, message.from_user.language_code,

        Chat.whitelist_data_provider, [channel_state_data['id'], search_query],
        Chat.whitelist_data_count_provider, [channel_state_data['id'], search_query],
        _PER_PAGE, 'nickname'
    )

    # Error processing
    if 'error' in chat_whitelist_page_data:
        if chat_whitelist_page_data['error'] in ['empty']:
            error = chat_whitelist_page_data['error'] if search_query is None else 'empty_search'
            error_message = localization.get_message(
                ['whitelist', 'errors', error],
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
    message_text = localization.get_message(['whitelist', 'list', 'text'], message.from_user.language_code)
    message_text += " " + localization.get_message(
        ['chat', 'show', 'text'], message.from_user.language_code, chat_name=chat_info['title'])
    message_text += '\n' + routing_helper_message

    # Chat buttons
    reply_markup = []
    for whitelist_data in chat_whitelist_page_data['data']:
        button_text = localization.get_message(
            ['whitelist', 'list', 'button', 'active' if whitelist_data['active'] else 'inactive'],
            message.from_user.language_code, nickname=whitelist_data['nickname'])

        reply_markup.append([{
            'text': button_text, 'callback_data': {'tp': 'allowed_user', 'id': whitelist_data['id']}}])

    if search_query is not None:
        reply_markup.append([{
            'text': localization.get_message(['buttons', 'clear_search'], message.from_user.language_code),
            'callback_data': {'tp': current_type, 'p': 1, 'search_query': None}}])

    # Navigation markup
    reply_markup.append(nav_layout)

    # Sending
    message_structures = [{
        'type': 'text',
        'text': message_text,
        'reply_markup': reply_markup
    }]
    await message_sender(message, resending=call is None, message_structures=message_structures)

    if change_user_state:
        UserStorage.change_page(message.chat.id, current_type)
        UserStorage.add_user_state_data(message.chat.id, current_type, {**whitelist_state_data, 'p': current_page})


# Show allowed user
async def show(call: telegram_types.CallbackQuery, message: telegram_types.Message, change_user_state=True, ignore_callback_data=False):
    allowed_user_state_data = state_data.get_state_data(
        call if not ignore_callback_data else None, message, routes.RouteMap.type('allowed_user'))
    chat_state_data = state_data.get_local_state_data(message, routes.RouteMap.type('chat'))

    if not len(allowed_user_state_data) or not len(chat_state_data):
        await notify(
            None, message, localization.get_message(['errors', 'state_data_none'], message.from_user.language_code))
        return

    allowed_user_data = AllowedUser.find(allowed_user_state_data['id'])
    if allowed_user_data is None:
        await notify(
            call, message, localization.get_message(['chat', 'errors', 'not_found'], message.from_user.language_code))
        return

    chat_info = await Chat.load_info(str(chat_state_data['service_id']))

    if 'error' in chat_info:
        await notify(call, message, localization.get_message(
            ['chat', 'errors', 'not_found_tg'], message.from_user.language_code))

    message_text = localization.get_message(
        ['allowed_user', 'show', 'text'], message.from_user.language_code,
        chat_name=chat_info['title'], nickname=allowed_user_data['nickname'])

    reply_markup = []

    state_button = {
        'text': localization.get_message(
            ['allowed_user', 'show', 'active_button', 'active' if allowed_user_data['active'] else 'inactive'],
            message.from_user.language_code,
        ), 'callback_data': {'tp': 'switch_active'}}
    reply_markup.append([state_button])

    reply_markup.append([{
        'text': localization.get_message(
            [
                'allowed_user', 'show', 'delete_button',
                'initial' if 'deleting' not in allowed_user_state_data else 'deleting'],
            message.from_user.language_code),
        'callback_data': {'tp': 'delete'}}])

    reply_markup.append([go_back_inline_button(message.from_user.language_code)])

    message_structures = [{
        'type': 'text',
        'text': message_text,
        'reply_markup': reply_markup
    }]
    await message_sender(message, message_structures=message_structures)

    if change_user_state:
        UserStorage.change_page(message.chat.id, routes.RouteMap.type('allowed_user'))
        UserStorage.add_user_state_data(message.chat.id, 'allowed_user', allowed_user_state_data | allowed_user_data)


async def switch_active(call: telegram_types.CallbackQuery, message: telegram_types.Message):
    allowed_user_state_data = state_data.get_local_state_data(message, routes.RouteMap.type('allowed_user'))
    if allowed_user_state_data is None:
        await raise_error(None, message, 'state_data_none')
        return

    new_active_values = AllowedUser.switch_active(allowed_user_state_data['id'])

    if new_active_values is None or new_active_values == allowed_user_state_data['active']:
        return

    allowed_user_state_data['active'] = new_active_values
    UserStorage.add_user_state_data(message.chat.id, 'allowed_user', allowed_user_state_data)

    # Tell show method to take data from state
    await show(call, message, change_user_state=False, ignore_callback_data=True)


async def delete(call: telegram_types.CallbackQuery, message: telegram_types.Message):
    allowed_user_state_data = state_data.get_local_state_data(message, routes.RouteMap.type('allowed_user'))
    if allowed_user_state_data is None:
        await raise_error(None, message, 'state_data_none')
        return

    # Already deleting
    if 'deleting' in allowed_user_state_data:
        deleted_id = AllowedUser.delete(allowed_user_state_data['id'])
        if deleted_id is not None:
            await chat_whitelist(call, message, change_user_state=False)
            UserStorage.go_back(message.chat.id, 'allowed_user')
            return

    allowed_user_state_data['deleting'] = True
    UserStorage.add_user_state_data(message.chat.id, 'allowed_user', allowed_user_state_data)

    await notify(call, message, localization.get_message(
        ['allowed_user', 'delete', 'confirm'], message.from_user.language_code), alert=True)

    await show(call, message)
