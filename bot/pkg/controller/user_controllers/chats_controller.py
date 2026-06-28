import typing

from framework.controller.types import ControllerParams

from framework.controller import state_data
from lib.language import localization
from framework.controller.message_tools import message_sender, go_back_inline_markup, is_call_or_command, \
    image_link_or_object, notify, go_back_inline_button, determine_search_query
from lib.python.dict_interface import validate_typed_dict_interface
from lib.telegram.aiogram.navigation_builder import NavigationBuilder
from pkg.config import routes
from pkg.controller.user_controllers.common_controller import chat_access_denied, raise_error
from pkg.service.user_storage import UserStorage
from pkg.service.chat import Chat
from project.types import ModeratedChatInterface

_PER_PAGE = 5
_MIN_RESTRICTION_DURATION_MINUTES = 1
_MAX_RESTRICTION_DURATION_MINUTES = 1440


async def add_chat(params: ControllerParams):
    call, message = params['call'], params['message']

    reply_add_chat_structure = {
        'type': 'text',
        'text': localization.get_message(
            ['add_chat', 'add_chat_reply_button_text'], params['language_code']),
        'markup_type': 'reply',
        'reply_markup': [[{
            'text': localization.get_message(
                ['add_chat', 'add_chat_reply_button'], params['language_code']),
            'request_id': 1, 'chat_is_channel': False, 'bot_is_member': True}]]
    }

    if is_call_or_command(call, message):
        message_structures = [{
            'type': 'image',
            'image': image_link_or_object(
                localization.get_link(['add_chat', 'anon_admin_example'], params['language_code'])),
            'text': localization.get_message(['add_chat', 'instruction'], params['language_code']),
            'reply_markup': go_back_inline_markup(params['language_code']),
            'parse_mode': 'HTML'
        }, reply_add_chat_structure]
        await message_sender(message.chat.id, message_structures=message_structures)

        return

    # ---
    # Chat adding

    if message.forward_from_chat is not None:
        chat_service_id = message.forward_from_chat.id
    elif message.chat_shared is not None:
        chat_service_id = message.chat_shared.chat_id
    else:
        chat_service_id = message.text

    result_connection = await Chat.add(chat_service_id, message.from_user.id)

    if 'error' in result_connection:
        if result_connection['error'] == 'connection_exists':
            result_connection = result_connection['connection']
        else:
            await chat_access_denied(call, message, result_connection)
            return False

    chat_info = await Chat.load_info(chat_service_id=str(chat_service_id))
    if 'error' in chat_info:
        await notify(call, message, localization.get_message(
            ['chat', 'errors', 'not_found_tg'], params['language_code']))
        return False

    reply_markup = [[{
        'text': localization.get_message(['buttons', 'go_to_settings'], params['language_code']),
        'callback_data': {'tp': 'chat', 'id': result_connection['moderated_chat_id']}
    }], [go_back_inline_button(params['language_code'])]]

    message_structures = [{
        'type': 'text',
        'text': localization.get_message(
            ['add_chat', 'success'], params['language_code']).format(chat_name=chat_info['title']),
        'reply_markup': reply_markup
    }, reply_add_chat_structure]

    await message_sender(message.chat.id, message_structures=message_structures)


async def my_chats(params: ControllerParams):
    call, message, current_state_data = params['call'], params['message'], params['state_data']

    current_state_data = determine_search_query(call, message, current_state_data)
    search_query = current_state_data.get('search_query', None)

    current_page, user_chat_page_data, routing_helper_message, nav_layout = \
        await NavigationBuilder().full_message_setup(
            call, message, current_state_data, params['route_name'], params['language_code'],

            Chat.data_provider_by_service_id, [message.chat.id, search_query],
            Chat.data_count_provider_by_service_id, [message.chat.id, search_query],
            _PER_PAGE, 'name'
        )

    # Error processing
    if 'error' in user_chat_page_data:
        if user_chat_page_data['error'] in ['empty']:
            error = user_chat_page_data['error'] if search_query is None else 'empty_search'
            error_message = localization.get_message(
                ['my_chats', 'errors', error],
                params['language_code'],
                command=routes.RouteMap.get_route_main_command('add_chat'))
        else:
            error_message = localization.get_message(
                ['navigation_builder', 'errors', user_chat_page_data['error']],
                params['language_code'])

        await notify(call, message, error_message, alert=True)
        return False

    # Building message
    message_text = localization.get_message(['my_chats', 'list', 'main'], params['language_code'])
    message_text += '\n' + routing_helper_message

    reply_markup = []

    # Chat buttons
    for chat_data in user_chat_page_data['data']:
        chat_info = await Chat.load_info(chat_service_id=str(chat_data['service_id']))

        if 'error' not in chat_info:
            button_text = localization.get_message(
                [
                    'my_chats', 'list', 'chat_button',
                    'active' if (chat_data['active'] and not chat_data['disabled'])
                    else ('disabled' if chat_data['disabled'] else 'inactive')
                ],
                params['language_code'], chat_name=chat_info['title'])
        else:
            button_text = localization.get_message(
                ['my_chats', 'list', 'chat_button', 'not_found_tg'], params['language_code']) \
                          + f" {chat_data['name']} {chat_data['service_id']}"

        button_data = {'tp': 'chat', 'id': chat_data['id']}

        reply_markup.append([{'text': button_text, 'callback_data': button_data}])

    if search_query is not None:
        reply_markup.append([{
            'text': localization.get_message(['buttons', 'clear_search'], params['language_code']),
            'callback_data': {'tp': params['route_name'], 'p': 1, 'search_query': None}
        }])

    # Navigation markup
    reply_markup.append(nav_layout)

    # Sending
    message_structures = [{
        'type': 'text',
        'text': message_text,
        'reply_markup': reply_markup
    }]
    await message_sender(message.chat.id, message_structures=message_structures)

    UserStorage.add_user_state_data(message.chat.id, params['route_name'], {**current_state_data, 'p': current_page})

    await Chat.update_names(message.chat.id)


async def show(params: ControllerParams):
    call, message = params['call'], params['message']

    if not len(params['state_data']):
        await raise_error(None, message, 'state_data_none')
        return

    # State data already have chat data
    if validate_typed_dict_interface(params['state_data'], ModeratedChatInterface, total=True):
        chat_data = params['state_data']
    else:
        chat_data = await Chat.find(params['state_data']['id'])

    if chat_data is None:
        await notify(
            call, message, localization.get_message(['chat', 'errors', 'not_found'], params['language_code']))
        return False

    chat_info = await Chat.load_info(str(chat_data['service_id']))

    if 'error' in chat_info:
        await notify(call, message, localization.get_message(
            ['chat', 'errors', 'not_found_tg'], params['language_code']))
        return False

    message_text = localization.get_message(
        ['chat', 'show', 'text'], params['language_code'], chat_name=chat_info['title'])
    if chat_info['nickname'] is not None:
        message_text += f" @{chat_info['nickname']}"

    if chat_data['disabled']:
        message_text += "\n\n" + localization.get_message(['chat', 'show', 'disabled'], params['language_code'])

    reply_markup = []
    add_to_whitelist_button = {
        'text': localization.get_message(['chat', 'show', 'add_to_whitelist_button'], params['language_code']),
        'callback_data': {'tp': 'add_to_chat_whitelist'}}
    reply_markup.append([add_to_whitelist_button])

    whitelist_button = {
        'text': localization.get_message(['chat', 'show', 'whitelist_button'], params['language_code']),
        'callback_data': {'tp': 'chat_whitelist'}}
    reply_markup.append([whitelist_button])

    restriction_duration_button = {
        'text': localization.get_message(
            ['chat', 'show', 'restriction_duration_button'],
            params['language_code'],
            duration=chat_data.get('restriction_duration_minutes', 5)),
        'callback_data': {'tp': 'chat_restriction_duration'}}
    reply_markup.append([restriction_duration_button])

    state_button = {
        'text': localization.get_message(
            [
                'chat', 'show', 'active_button',
                'active' if chat_data['active'] else 'inactive'],
            params['language_code'],
        ), 'callback_data': {'tp': 'switch_active'}}
    reply_markup.append([state_button])

    delete_button = {
        'text': localization.get_message(
            [
                'chat', 'show', 'delete_button',
                'deleting' if params['state_data'].get('deleting') else 'initial'
            ],
            params['language_code']),
        'callback_data': {'tp': 'delete'}}
    reply_markup.append([delete_button])

    reply_markup.append([go_back_inline_button(params['language_code'])])

    message_structures = [{
        'type': 'text',
        'text': message_text,
        'reply_markup': reply_markup
    }]
    await message_sender(message.chat.id, message_structures=message_structures)

    UserStorage.add_user_state_data(message.chat.id, 'chat', {**params['state_data'], **chat_data})


async def restriction_duration(params: ControllerParams):
    call, message = params['call'], params['message']
    chat_state_data = state_data.get_local_state_data(message, routes.RouteMap.type('chat'))

    if 'id' not in chat_state_data:
        await raise_error(None, message, 'state_data_none')
        return False

    if is_call_or_command(call, message):
        chat_data = await Chat.find(chat_state_data['id'])
        if chat_data is None:
            await notify(
                call, message, localization.get_message(['chat', 'errors', 'not_found'], params['language_code']))
            return False

        restriction_access = await Chat.validate_restriction_access(int(chat_data['service_id']))
        if 'error' in restriction_access:
            await notify(call, message, localization.get_message(
                ['chat', 'restriction_duration', 'warnings', restriction_access['error']],
                params['language_code']), alert=True)

        message_structures = [{
            'type': 'text',
            'text': localization.get_message(
                ['chat', 'restriction_duration', 'text'],
                params['language_code'],
                duration=chat_data.get('restriction_duration_minutes', 5),
                min_duration=_MIN_RESTRICTION_DURATION_MINUTES,
                max_duration=_MAX_RESTRICTION_DURATION_MINUTES),
            'reply_markup': go_back_inline_markup(params['language_code']),
            'parse_mode': 'HTML'
        }]
        await message_sender(message.chat.id, message_structures=message_structures)
        return

    try:
        duration_minutes = int(message.text)
    except ValueError:
        await notify(None, message, localization.get_message(
            ['chat', 'restriction_duration', 'errors', 'invalid'],
            params['language_code'],
            min_duration=_MIN_RESTRICTION_DURATION_MINUTES,
            max_duration=_MAX_RESTRICTION_DURATION_MINUTES), save_state=True, button_text='cancel')
        return False

    if (
            duration_minutes < _MIN_RESTRICTION_DURATION_MINUTES
            or duration_minutes > _MAX_RESTRICTION_DURATION_MINUTES):
        await notify(None, message, localization.get_message(
            ['chat', 'restriction_duration', 'errors', 'invalid'],
            params['language_code'],
            min_duration=_MIN_RESTRICTION_DURATION_MINUTES,
            max_duration=_MAX_RESTRICTION_DURATION_MINUTES), save_state=True, button_text='cancel')
        return False

    duration_minutes = await Chat.update_restriction_duration(chat_state_data['id'], duration_minutes)
    chat_state_data['restriction_duration_minutes'] = duration_minutes
    UserStorage.add_user_state_data(message.chat.id, 'chat', chat_state_data)

    chat_data = await Chat.find(chat_state_data['id'])
    if chat_data is None:
        await notify(
            None, message, localization.get_message(['chat', 'errors', 'not_found'], params['language_code']))
        return False

    restriction_access = await Chat.validate_restriction_access(int(chat_data['service_id']))
    if 'error' in restriction_access:
        result_message = localization.get_message(
            ['chat', 'restriction_duration', 'success_with_warning'],
            params['language_code'],
            duration=duration_minutes)
        result_message += "\n\n" + localization.get_message(
            ['chat', 'restriction_duration', 'warnings', restriction_access['error']],
            params['language_code'])
    else:
        result_message = localization.get_message(
            ['chat', 'restriction_duration', 'success'],
            params['language_code'],
            duration=duration_minutes)

    await notify(None, message, result_message, save_state=True)


async def switch_active(params: ControllerParams):
    call, message, current_state_data = params['call'], params['message'], params['state_data']

    if current_state_data is None:
        await notify(
            call, message, localization.get_message(['errors', 'state_data_none'], params['language_code']))
        return False

    new_active_values = await Chat.switch_active(current_state_data['id'])

    if new_active_values is None or new_active_values == current_state_data['active']:
        return

    current_state_data['active'] = new_active_values

    params['state_data'] = current_state_data
    UserStorage.add_user_state_data(message.chat.id, 'chat', params['state_data'])

    # Tell show method to take data from state
    await show(params)


async def delete(params: ControllerParams):
    call, message, current_state_data = params['call'], params['message'], params['state_data']

    if current_state_data is None or 'id' not in current_state_data:
        await raise_error(None, message, 'state_data_none')
        return

    # Already deleting
    if 'deleting' in current_state_data:
        delete_result = await Chat.delete(current_state_data['id'], message.chat.id)
        if isinstance(delete_result, dict) and 'error' in delete_result:
            await chat_access_denied(call, message, delete_result)
            return False

        if delete_result is not None:
            await params['go_back_action'](call)
            return

    current_state_data['deleting'] = True

    params['state_data'] = current_state_data
    UserStorage.add_user_state_data(message.chat.id, 'chat', params['state_data'])

    await notify(call, message, localization.get_message(
        ['chat', 'delete', 'confirm'], params['language_code']), alert=True)

    await show(params)
