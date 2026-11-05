import datetime
import html
from framework.controller.types import ControllerParams
from framework.system import telegram_types

from framework.controller.message_tools import notify, message_sender, is_call_or_command, go_back_inline_markup, \
    go_back_inline_button, determine_search_query
from framework.controller import state_data
from lib.language import localization
from lib.python.dict_interface import validate_typed_dict_interface
from lib.telegram.aiogram.navigation_builder import NavigationBuilder
from pkg.config import routes
from pkg.controller.user_controllers.chats_controller import _PER_PAGE
from pkg.controller.user_controllers.common_controller import raise_error
from pkg.service.allowed_user import AllowedUser, parse_members
from pkg.service.chat import Chat
from pkg.service.member_alerts import format_date, member_label
from pkg.service.tariff import Tariff
from pkg.service.user_storage import UserStorage
from project.types import AllowedUserInterface


_TERM_CHOICES = (0, 7, 30)  # days; 0: for good


def member_text(entry: dict) -> str:
    """A whitelist entry in plain text: @nickname, else the name, else the id."""
    if entry.get('nickname'):
        return '@' + entry['nickname']
    return entry.get('display_name') or f"id {entry.get('user_service_id')}"


def _add_markup(language_code: str) -> list:
    return [[{'text': localization.get_message(['chat', 'add_to_whitelist', 'pick_button'], language_code),
              'request_users': {'request_id': 2, 'max_quantity': 10}}]]


# Add user to whitelist
async def add_to_chat_whitelist(params: ControllerParams):
    call, message = params['call'], params['message']
    language_code = params['language_code']

    if is_call_or_command(call, message):
        await message_sender(message.chat.id, message_structures=[{
            'type': 'text',
            'text': localization.get_message(['chat', 'add_to_whitelist', 'text'], language_code),
            'reply_markup': go_back_inline_markup(language_code),
            'parse_mode': 'HTML'
        }, {
            'type': 'text',
            'text': localization.get_message(['chat', 'add_to_whitelist', 'pick_hint'], language_code),
            'markup_type': 'reply',
            'reply_markup': _add_markup(language_code)
        }])
        return

    # ---
    # User adding

    chat_state_data = state_data.get_local_state_data(message, 'chat')
    members, unknown, days = parse_members(message)
    if days and members and not Tariff.is_paid(await Chat.owner_tariff_id(chat_state_data['id'])):
        await notify(None, message, localization.get_message(['alerts', 'paid_only'], language_code),
                     save_state=True)
        return

    added = []
    for member in members:
        result = await AllowedUser.allow(chat_state_data['id'], **member, days=days)
        if result is None:
            await notify(call, message, localization.get_message(['errors', 'unexpected'], language_code),
                         alert=True, button_text='cancel')
            return False
        added.append(member_text(member))

    lines = []
    if added:
        if days:
            lines.append(localization.get_message(
                ['chat', 'add_to_whitelist', 'success_list_until'], language_code, members=', '.join(added),
                date=format_date(datetime.datetime.now() + datetime.timedelta(days=days))))
        else:
            lines.append(localization.get_message(
                ['chat', 'add_to_whitelist', 'success_list'], language_code, members=', '.join(added)))
    if unknown:
        lines.append(localization.get_message(
            ['chat', 'add_to_whitelist', 'not_understood'], language_code, words=', '.join(unknown)))
    lines.append(localization.get_message(['chat', 'add_to_whitelist', 'more'], language_code))

    await message_sender(message.chat.id, message_structures=[{
        'type': 'text',
        'text': '\n\n'.join(lines),
        'reply_markup': go_back_inline_markup(language_code)
    }, {
        'type': 'text',
        'text': localization.get_message(['chat', 'add_to_whitelist', 'pick_hint'], language_code),
        'markup_type': 'reply',
        'reply_markup': _add_markup(language_code)
    }])


# Show chat whitelist
async def chat_whitelist(params: ControllerParams):
    call, message, current_state_data = params['call'], params['message'], params['state_data']

    # Getting data and full navigation setup
    chat = state_data.get_local_state_data(message, routes.RouteMap.type('chat'))

    current_state_data = determine_search_query(call, message, current_state_data)
    search_query = current_state_data.get('search_query', None)

    chat_info = await Chat.load_info(str(chat['service_id']))

    current_page, chat_whitelist_page_data, routing_helper_message, nav_layout = \
        await NavigationBuilder().full_message_setup(
            call, message, current_state_data, params['route_name'], params['language_code'],

            Chat.whitelist_data_provider, [chat['id'], search_query],
            Chat.whitelist_data_count_provider, [chat['id'], search_query],
            _PER_PAGE, 'nickname'
        )

    # Error processing
    if 'error' in chat_whitelist_page_data:
        if chat_whitelist_page_data['error'] in ['empty']:

            # Returning from user and something changed (for example, after delete)
            if params['is_step_back']:
                # 1. search result gives nothing – just try again with new state without search query
                if search_query is not None:
                    UserStorage.del_user_state_data(message.chat.id, params['route_name'])
                    params['state_data'] = {}
                    return await chat_whitelist(params)
                # 2. Act like message, use message notification approach
                else:
                    call = None

            error = chat_whitelist_page_data['error'] if search_query is None else 'empty_search'
            error_message = localization.get_message(
                ['whitelist', 'errors', error],
                params['language_code'],
                command=routes.RouteMap.get_route_main_command('add_chat'))

            # When already opened, message (or go_back without search) and not results at all, save state
            await notify(
                call, message, error_message,
                alert=True, save_state=search_query is None)

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
    if chat_info['nickname'] is not None:
        message_text += f" @{chat_info['nickname']}"
    message_text += '\n' + routing_helper_message

    # Chat buttons
    reply_markup = []
    for whitelist_data in chat_whitelist_page_data['data']:
        button_text = localization.get_message(
            ['whitelist', 'list', 'button', 'active' if whitelist_data['active'] else 'inactive'],
            params['language_code'], nickname=member_text(whitelist_data))
        if whitelist_data.get('expires_at') is not None:
            button_text += ' · ' + localization.get_message(
                ['allowed_user', 'show', 'term', 'until_short'], params['language_code'],
                date=format_date(whitelist_data['expires_at']))

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
    await message_sender(message.chat.id, message_structures=message_structures)

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
        allowed_user_data = await AllowedUser.find(params['state_data']['id'])

    if allowed_user_data is None:
        await notify(
            call, message, localization.get_message(['chat', 'errors', 'not_found'], params['language_code']))
        return False

    chat_info = await Chat.load_info(str(chat_state_data['service_id']))

    if 'error' in chat_info:
        await notify(call, message, localization.get_message(
            ['chat', 'errors', 'not_found_tg'], params['language_code']))
        return False

    language_code = params['language_code']
    message_text = localization.get_message(
        ['allowed_user', 'show', 'text'], language_code, chat_name=html.escape(chat_info['title']),
        member=member_label(allowed_user_data.get('nickname'), allowed_user_data.get('display_name'),
                            allowed_user_data.get('user_service_id')))
    expires_at = allowed_user_data.get('expires_at')
    if expires_at is None:
        message_text += "\n" + localization.get_message(['allowed_user', 'show', 'term', 'forever'], language_code)
    elif expires_at <= datetime.datetime.now():
        message_text += "\n" + localization.get_message(
            ['allowed_user', 'show', 'term', 'ended'], language_code, date=format_date(expires_at))
    else:
        message_text += "\n" + localization.get_message(
            ['allowed_user', 'show', 'term', 'until'], language_code, date=format_date(expires_at))
    if not allowed_user_data.get('user_service_id'):
        message_text += "\n\n" + localization.get_message(['allowed_user', 'show', 'no_id_hint'], language_code)

    reply_markup = []

    state_button = {
        'text': localization.get_message(
            ['allowed_user', 'show', 'active_button', 'active' if allowed_user_data['active'] else 'inactive'],
            language_code,
        ), 'callback_data': {'tp': 'switch_active'}}
    reply_markup.append([state_button])

    paid = Tariff.is_paid(await Chat.owner_tariff_id(chat_state_data['id']))
    reply_markup.append([{
        'text': ('' if paid or days == 0 else localization.get_message(['chat', 'show', 'locked'], language_code))
        + localization.get_message(['allowed_user', 'show', 'term_button', 'forever' if days == 0 else 'days'],
                                   language_code, days=days),
        'callback_data': {'tp': 'set_term', 'd': days}} for days in _TERM_CHOICES])

    reply_markup.append([{
        'text': localization.get_message(
            [
                'allowed_user', 'show', 'delete_button',
                'initial' if 'deleting' not in params['state_data'] else 'deleting'],
            language_code),
        'callback_data': {'tp': 'delete'}}])

    reply_markup.append([go_back_inline_button(params['language_code'])])

    message_structures = [{
        'type': 'text',
        'text': message_text,
        'reply_markup': reply_markup,
        'parse_mode': 'HTML',
        'disable_web_page_preview': True
    }]
    await message_sender(message.chat.id, message_structures=message_structures)

    UserStorage.add_user_state_data(message.chat.id, 'allowed_user', {**params['state_data'], **allowed_user_data})


async def switch_active(params: ControllerParams):
    call, message, current_state_data = params['call'], params['message'], params['state_data']

    if current_state_data is None:
        await raise_error(None, message, 'state_data_none')
        return

    new_active_values = await AllowedUser.switch_active(current_state_data['id'])

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
        deleted_id = await AllowedUser.delete(current_state_data['id'])
        if deleted_id is not None:
            await params['go_back_action'](call)
            return

    current_state_data['deleting'] = True

    params['state_data'] = current_state_data
    UserStorage.add_user_state_data(message.chat.id, 'allowed_user', params['state_data'])

    await notify(call, message, localization.get_message(
        ['allowed_user', 'delete', 'confirm'], params['language_code']), alert=True)

    await show(params)


async def set_term(params: ControllerParams):
    """How long the member may write: for good, or 7 or 30 days from now (timed access is a paid feature)."""
    call, message, current_state_data = params['call'], params['message'], params['state_data']
    language_code = params['language_code']
    chat_state_data = state_data.get_local_state_data(message, routes.RouteMap.type('chat'))
    days = int(current_state_data.pop('d', 0) or 0)

    if days and not Tariff.is_paid(await Chat.owner_tariff_id(chat_state_data['id'])):
        await notify(call, message, localization.get_message(['alerts', 'paid_only'], language_code), alert=True)
        return

    updated = await AllowedUser.set_term(current_state_data['id'], days)
    if updated is None:
        await raise_error(call, message, 'unexpected')
        return
    await notify(call, message, localization.get_message(
        ['allowed_user', 'show', 'term_toast', 'forever' if days == 0 else 'days'], language_code, days=days))
    current_state_data.pop('deleting', None)
    params['state_data'] = {**current_state_data, **dict(updated)}
    UserStorage.add_user_state_data(message.chat.id, 'allowed_user', params['state_data'])
    await show(params)
