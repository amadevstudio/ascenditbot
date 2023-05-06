from framework.controller.types import ControllerParams

from framework.controller.message_tools import notify, message_sender, is_call_or_command, go_back_inline_markup, \
    go_back_inline_button, determine_search_query
from framework.controller import state_data
from lib.language import localization
from lib.python.dict_interface import validate_typed_dict_interface
from lib.telegram.aiogram.navigation_builder import NavigationBuilder
from pkg.config import routes
from pkg.controller.user_controllers.chats_controller import _PER_PAGE
from pkg.controller.user_controllers.common_controller import raise_error
from pkg.service.allowed_user import AllowedUser
from pkg.service.chat import Chat
from pkg.service.user_storage import UserStorage
from project.types import AllowedUserInterface


# Add user to whitelist
async def add_to_chat_whitelist(params: ControllerParams):
    call, message = params['call'], params['message']

    if is_call_or_command(call, message):
        message_structures = [{
            'type': 'text',
            'text': localization.get_message(['chat', 'add_to_whitelist', 'text'], params['language_code']),
            'reply_markup': go_back_inline_markup(params['language_code']),
            'parse_mode': 'HTML'
        }]
        await message_sender(message, resending=call is None, message_structures=message_structures)

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
        error_trace = ['errors', result_connection['error']]  # == 'unexpected'
        # if result_connection['error'] == 'unexpected':
        #     error_trace = ['errors', result_connection['error']]
        # else:
        #     error_trace = ['chat', 'add_to_whitelist', 'errors', result_connection['error']]
        await notify(
            call, message, localization.get_message(error_trace, params['language_code']),
            alert=True, button_text='cancel')
        return False

    message_structures = [{
        'type': 'text',
        'text': localization.get_message(
            ['chat', 'add_to_whitelist', 'success'], params['language_code']).format(nickname=user_nickname),
        'reply_markup': go_back_inline_markup(params['language_code'])
    }]

    await message_sender(message, resending=call is None, message_structures=message_structures)


# Show chat whitelist
async def chat_whitelist(params: ControllerParams):
    call, message, current_state_data = params['call'], params['message'], params['state_data']

    # Getting data and full navigation setup
    chat = state_data.get_local_state_data(message, routes.RouteMap.type('chat'))

    current_state_data = determine_search_query(call, message, current_state_data)
    search_query = current_state_data.get('search_query', None)

    chat_info = await Chat.load_info(str(chat['service_id']))

    current_page, chat_whitelist_page_data, routing_helper_message, nav_layout = NavigationBuilder().full_message_setup(
        call, message, current_state_data, params['route_name'], params['language_code'],

        Chat.whitelist_data_provider, [chat['id'], search_query],
        Chat.whitelist_data_count_provider, [chat['id'], search_query],
        _PER_PAGE, 'nickname'
    )

    # Error processing
    if 'error' in chat_whitelist_page_data:
        if chat_whitelist_page_data['error'] in ['empty']:
            print("h1", flush=True)
            # Returning from user and something changed (for example, after delete)
            if params['is_step_back']:
                print("h2", flush=True)
                # 1. search result gives nothing – just try again with new state without search query
                if search_query is not None:
                    UserStorage.del_user_state_data(message.chat.id, params['route_name'])
                    params['state_data'] = {}
                    return await chat_whitelist(params)
                # 2. Act like message, will resend
                else:
                    call = None

            error = chat_whitelist_page_data['error'] if search_query is None else 'empty_search'
            error_message = localization.get_message(
                ['whitelist', 'errors', error],
                params['language_code'],
                command=routes.RouteMap.get_route_main_command('add_chat'))

            # When already opened, message (or go_back without search) and not results at all, save state
            await notify(call, message, error_message, alert=True, save_state=search_query is None)

        else:
            error_message = localization.get_message(
                ['navigation_builder', 'errors', chat_whitelist_page_data['error']],
                params['language_code'])
            await notify(call, message, error_message, alert=True)

        return False

    # Building message
    message_text = localization.get_message(['whitelist', 'list', 'text'], params['language_code'])
    message_text += " " + localization.get_message(
        ['chat', 'show', 'text'], params['language_code'], chat_name=chat_info['title'])
    message_text += '\n' + routing_helper_message

    # Chat buttons
    reply_markup = []
    for whitelist_data in chat_whitelist_page_data['data']:
        button_text = localization.get_message(
            ['whitelist', 'list', 'button', 'active' if whitelist_data['active'] else 'inactive'],
            params['language_code'], nickname=whitelist_data['nickname'])

        reply_markup.append([{
            'text': button_text, 'callback_data': {'tp': 'allowed_user', 'id': whitelist_data['id']}}])

    if search_query is not None:
        reply_markup.append([{
            'text': localization.get_message(['buttons', 'clear_search'], params['language_code']),
            'callback_data': {'tp': params['route_name'], 'p': 1, 'search_query': None}}])

    # Navigation markup
    reply_markup.append(nav_layout)

    # Sending
    message_structures = [{
        'type': 'text',
        'text': message_text,
        'reply_markup': reply_markup
    }]
    await message_sender(message, resending=call is None, message_structures=message_structures)

    UserStorage.add_user_state_data(message.chat.id, params['route_name'], {**current_state_data, 'p': current_page})


# Show allowed user
async def show(params: ControllerParams):
    call, message = params['call'], params['message']

    chat_state_data = state_data.get_local_state_data(message, routes.RouteMap.type('chat'))

    if not len(params['state_data']) or not len(chat_state_data):
        await notify(
            None, message, localization.get_message(['errors', 'state_data_none'], params['language_code']))
        return False

    # State data already have chat data
    if validate_typed_dict_interface(params['state_data'], AllowedUserInterface, total=True):
        allowed_user_data = params['state_data']
    else:
        allowed_user_data = AllowedUser.find(params['state_data']['id'])

    if allowed_user_data is None:
        await notify(
            call, message, localization.get_message(['chat', 'errors', 'not_found'], params['language_code']))
        return False

    chat_info = await Chat.load_info(str(chat_state_data['service_id']))

    if 'error' in chat_info:
        await notify(call, message, localization.get_message(
            ['chat', 'errors', 'not_found_tg'], params['language_code']))
        return False

    message_text = localization.get_message(
        ['allowed_user', 'show', 'text'], params['language_code'],
        chat_name=chat_info['title'], nickname=allowed_user_data['nickname'])

    reply_markup = []

    state_button = {
        'text': localization.get_message(
            ['allowed_user', 'show', 'active_button', 'active' if allowed_user_data['active'] else 'inactive'],
            params['language_code'],
        ), 'callback_data': {'tp': 'switch_active'}}
    reply_markup.append([state_button])

    reply_markup.append([{
        'text': localization.get_message(
            [
                'allowed_user', 'show', 'delete_button',
                'initial' if 'deleting' not in params['state_data'] else 'deleting'],
            params['language_code']),
        'callback_data': {'tp': 'delete'}}])

    reply_markup.append([go_back_inline_button(params['language_code'])])

    message_structures = [{
        'type': 'text',
        'text': message_text,
        'reply_markup': reply_markup
    }]
    await message_sender(message, message_structures=message_structures)

    UserStorage.add_user_state_data(message.chat.id, 'allowed_user', {**params['state_data'], **allowed_user_data})


async def switch_active(params: ControllerParams):
    call, message, current_state_data = params['call'], params['message'], params['state_data']

    if current_state_data is None:
        await raise_error(None, message, 'state_data_none')
        return

    new_active_values = AllowedUser.switch_active(current_state_data['id'])

    if new_active_values is None or new_active_values == current_state_data['active']:
        return

    current_state_data['active'] = new_active_values

    params['state_data'] = current_state_data
    UserStorage.add_user_state_data(message.chat.id, 'allowed_user', params['state_data'])

    await show(params)


async def delete(params: ControllerParams):
    call, message, current_state_data = params['call'], params['message'], params['state_data']

    if current_state_data is None:
        await raise_error(None, message, 'state_data_none')
        return

    # Already deleting
    if 'deleting' in current_state_data:
        deleted_id = AllowedUser.delete(current_state_data['id'])
        if deleted_id is not None:
            await params['go_back_action'](call)
            return

    current_state_data['deleting'] = True

    params['state_data'] = current_state_data
    UserStorage.add_user_state_data(message.chat.id, 'allowed_user', params['state_data'])

    await notify(call, message, localization.get_message(
        ['allowed_user', 'delete', 'confirm'], params['language_code']), alert=True)

    await show(params)
