from framework.system import telegram_types

from framework.controller import state_data
from lib.language import localization
from framework.controller.message_tools import message_sender, go_back_inline_markup, is_call_or_command, \
    image_link_or_object, notify, go_back_inline_button, determine_search_query
from lib.telegram.aiogram.navigation_builder import NavigationBuilder
from pkg.config import routes
from pkg.controller.user_controllers.common_controller import chat_access_denied, raise_error
from pkg.service.user_storage import UserStorage
from pkg.service.chat import Chat

_PER_PAGE = 5


async def add_chat(call: telegram_types.CallbackQuery, message: telegram_types.Message, change_user_state=True):
    if is_call_or_command(call, message):
        message_structures = [{
            'type': 'image',
            'image': image_link_or_object(
                localization.get_link(['add_chat', 'anon_admin_example'], message.from_user.language_code)),
            'text': localization.get_message(['add_chat', 'instruction'], message.from_user.language_code),
            'reply_markup': go_back_inline_markup(message.from_user.language_code),
            'parse_mode': 'HTML'
        }]
        await message_sender(message, resending=call is None, message_structures=message_structures)

        if change_user_state:
            UserStorage.change_page(message.chat.id, routes.RouteMap.type('add_chat'))

        return

    # ---
    # Chat adding

    if message.forward_from_chat is not None:
        chat_service_id = message.forward_from_chat.id
    else:
        chat_service_id = message.text

    result_connection = await Chat.add(chat_service_id, message.from_user.id)

    if 'error' in result_connection:
        if result_connection['error'] == 'connection_exists':
            result_connection = result_connection['connection']
        else:
            await chat_access_denied(call, message, result_connection)
            return

    chat_info = await Chat.load_info(chat_service_id=str(chat_service_id))
    if 'error' in chat_info:
        await notify(call, message, localization.get_message(
            ['chat', 'errors', 'not_found_tg'], message.from_user.language_code))

    reply_markup = [[{
        'text': localization.get_message(['buttons', 'go_to_settings'], message.from_user.language_code),
        'callback_data': {'tp': 'chat', 'id': result_connection['moderated_chat_id']}
    }], [go_back_inline_button(message.from_user.language_code)]]

    message_structures = [{
        'type': 'text',
        'text': localization.get_message(
            ['add_chat', 'success'], message.from_user.language_code).format(chat_name=chat_info['title']),
        'reply_markup': reply_markup
    }]

    await message_sender(message, resending=call is None, message_structures=message_structures)


async def my_chats(call: telegram_types.CallbackQuery, message: telegram_types.Message, change_user_state=True):
    current_type = routes.RouteMap.type('my_chats')

    # Getting data and full navigation setup
    current_state_data = state_data.get_state_data(call, message, current_type)

    current_state_data = determine_search_query(call, message, current_state_data)
    search_query = current_state_data.get('search_query', None)

    current_page, user_chat_page_data, routing_helper_message, nav_layout = NavigationBuilder().full_message_setup(
        call, message, current_state_data, current_type, message.from_user.language_code,

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
                message.from_user.language_code,
                command=routes.RouteMap.get_route_main_command('add_chat'))
        else:
            error_message = localization.get_message(
                ['navigation_builder', 'errors', user_chat_page_data['error']],
                message.from_user.language_code)
        await notify(
            call, message, error_message, alert=True)
        return

    # Building message
    message_text = localization.get_message(['my_chats', 'list', 'main'], message.from_user.language_code)
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
                message.from_user.language_code, chat_name=chat_info['title'])
        else:
            button_text = localization.get_message(
                ['my_chats', 'list', 'chat_button', 'not_found_tg'], message.from_user.language_code) \
                          + f" {chat_data['name']} {chat_data['service_id']}"

        button_data = {'tp': 'chat', 'id': chat_data['id']}

        reply_markup.append([{'text': button_text, 'callback_data': button_data}])

    if search_query is not None:
        reply_markup.append([{
            'text': localization.get_message(['buttons', 'clear_search'], message.from_user.language_code),
            'callback_data': {'tp': current_type, 'p': 1, 'search_query': None}
        }])

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
        UserStorage.add_user_state_data(message.chat.id, current_type, {**current_state_data, 'p': current_page})

    await Chat.update_names(message.chat.id)


async def show(call: telegram_types.CallbackQuery, message: telegram_types.Message, change_user_state=True):
    chat_income_data = state_data.get_current_state_data(call, message, 'chat')

    if not len(chat_income_data):
        await raise_error(None, message, 'state_data_none')
        return

    chat_data = Chat.find(chat_income_data['id'])
    if chat_data is None:
        await notify(
            call, message, localization.get_message(['chat', 'errors', 'not_found'], message.from_user.language_code))
        return

    chat_info = await Chat.load_info(str(chat_data['service_id']))

    if 'error' in chat_info:
        await notify(call, message, localization.get_message(
            ['chat', 'errors', 'not_found_tg'], message.from_user.language_code))

    message_text = localization.get_message(
        ['chat', 'show', 'text'], message.from_user.language_code, chat_name=chat_info['title'])

    if chat_data['disabled']:
        message_text += "\n\n" + localization.get_message(['chat', 'show', 'disabled'], message.from_user.language_code)

    reply_markup = []
    add_to_whitelist_button = {
        'text': localization.get_message(['chat', 'show', 'add_to_whitelist_button'], message.from_user.language_code),
        'callback_data': {'tp': 'add_to_chat_whitelist'}}
    reply_markup.append([add_to_whitelist_button])

    whitelist_button = {
        'text': localization.get_message(['chat', 'show', 'whitelist_button'], message.from_user.language_code),
        'callback_data': {'tp': 'chat_whitelist'}}
    reply_markup.append([whitelist_button])

    state_button = {
        'text': localization.get_message(
            [
                'chat', 'show', 'active_button',
                'active' if chat_data['active'] else 'inactive'],
            message.from_user.language_code,
        ), 'callback_data': {'tp': 'switch_active'}}
    reply_markup.append([state_button])

    reply_markup.append([go_back_inline_button(message.from_user.language_code)])

    message_structures = [{
        'type': 'text',
        'text': message_text,
        'reply_markup': reply_markup
    }]
    await message_sender(message, message_structures=message_structures)

    if change_user_state:
        UserStorage.change_page(message.chat.id, routes.RouteMap.type('chat'))
        UserStorage.add_user_state_data(message.chat.id, 'chat', chat_data)


async def switch_active(call: telegram_types.CallbackQuery, message: telegram_types.Message):
    chat_state_data = state_data.get_local_state_data(message, 'chat')
    if chat_state_data is None:
        await notify(
            None, message, localization.get_message(['errors', 'state_data_none'], message.from_user.language_code))
        return

    new_active_values = Chat.switch_active(chat_state_data['id'])

    if new_active_values is None or new_active_values == chat_state_data['active']:
        return

    chat_state_data['active'] = new_active_values
    UserStorage.add_user_state_data(message.chat.id, 'chat', chat_state_data)

    # Tell show method to take data from state
    call.data = {}
    await show(call, message, change_user_state=False)
