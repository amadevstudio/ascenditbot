import html
import typing

from framework.controller.types import ControllerParams
from framework.system import telegram_types

from framework.controller import state_data
from lib.language import localization
from framework.controller.message_tools import message_sender, go_back_inline_markup, is_call_or_command, \
    notify, go_back_inline_button, determine_search_query
from lib.python.dict_interface import validate_typed_dict_interface
from lib.telegram.aiogram.navigation_builder import NavigationBuilder
from pkg.config import routes
from pkg.controller.user_controllers.common_controller import chat_access_denied, raise_error
from pkg.service.user_storage import UserStorage
from pkg.service.channel_bonus import ChannelBonus
from pkg.service.chat import Chat
from pkg.service.user import User
from pkg.service import group_connect, post_limit
from pkg.service.access import outsiders_mode
from pkg.service.tariff import Tariff
from project.i18n_owner_tools import ADD_TO_GROUP_URL
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
            # Any group the user may give the bot rights in: Telegram adds the bot as an admin with these rights
            'request_id': 1, 'chat_is_channel': False,
            'user_administrator_rights': group_connect.USER_RIGHTS,
            'bot_administrator_rights': group_connect.BOT_RIGHTS}]]
    }

    if is_call_or_command(call, message):
        # The add-to-group link asks Telegram to make the bot an admin with the rights it needs; once it is,
        # the group router connects the group and sends its page (my_chat_member)
        message_structures = [{
            'type': 'text',
            'text': localization.get_message(['add_chat', 'instruction'], params['language_code']),
            'reply_markup': [
                [{'text': localization.get_message(['add_chat', 'add_to_group_button'], params['language_code']),
                  'url': ADD_TO_GROUP_URL}],
                *go_back_inline_markup(params['language_code'])],
            'parse_mode': 'HTML'
        }, reply_add_chat_structure]
        await message_sender(message.chat.id, message_structures=message_structures)

        return

    # ---
    # Chat adding

    # Bot API 7.0 replaced forward_from_chat with forward_origin: a message an anonymous admin sent in a group
    # carries the group as sender_chat (MessageOriginChat), a channel post carries chat (MessageOriginChannel)
    forward_origin = message.forward_origin
    forwarded_chat = getattr(forward_origin, 'sender_chat', None) or getattr(forward_origin, 'chat', None)
    if forwarded_chat is not None:
        chat_service_id = forwarded_chat.id
    elif message.chat_shared is not None:
        chat_service_id = message.chat_shared.chat_id
    else:
        chat_service_id = message.text

    if not chat_service_id:
        await notify(call, message, localization.get_message(
            ['chat', 'errors', 'not_found_tg'], params['language_code']))
        return False

    # Picked with the button, the bot is being added right now: a few tries while Telegram makes it an admin
    if message.chat_shared is not None:
        connected = await group_connect.connect_soon(chat_service_id, message.from_user.id)
    else:
        connected = await group_connect.connect(chat_service_id, message.from_user.id)
    if 'error' in connected:
        await chat_access_denied(call, message, connected)
        return False

    # my_chat_member may have shown the group already
    if not group_connect.first_to_announce(connected['moderated_chat_id'], message.from_user.id):
        return
    chat_data = await Chat.find(connected['moderated_chat_id'])
    await message_sender(message.chat.id, message_structures=[{
        'type': 'text', 'parse_mode': 'HTML',
        'text': localization.get_message(['group', 'auto_connected'], params['language_code'],
                                         chat_name=html.escape(await Chat.name_of(chat_data) if chat_data else ''))}])
    await open_chat_page(message, connected['moderated_chat_id'], params['language_code'])


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
            working = chat_data['active'] and not chat_data['disabled']
            # On, but the owner took the bot's rights away: nothing is moderated there, so no ✅
            if working and await Chat.bot_rights_problem(chat_data['service_id']):
                state = 'no_rights'
            else:
                state = 'active' if working else ('disabled' if chat_data['disabled'] else 'inactive')
            button_text = localization.get_message(
                ['my_chats', 'list', 'chat_button', state], params['language_code'], chat_name=chat_info['title'])
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


async def open_chat_page(message: telegram_types.Message, chat_id: int, language_code: str | None) -> bool:
    """Opens a group's page in the private chat from outside the menu (a deep link, a command in the group):
    the menu, the list and the group, so Back leads to the list."""
    user_chat_id = message.chat.id
    chat_data = await Chat.find(chat_id)
    if chat_data is None:
        return False
    access = await Chat.validate_access(int(chat_data['service_id']), user_chat_id)
    if 'error' in access:
        await chat_access_denied(None, message, access)
        return False

    UserStorage.new_navigation_journey(user_chat_id, 'menu')
    UserStorage.change_page(user_chat_id, 'my_chats')
    UserStorage.add_user_state_data(user_chat_id, 'chat', {'id': chat_id})
    UserStorage.set_resend(user_chat_id)
    params: ControllerParams = {
        'call': None, 'message': message, 'route_name': 'chat', 'state_data': {'id': chat_id},
        'is_step_back': False, 'go_back_action': None, 'language_code': language_code}
    if await show(params) is False:
        return False
    UserStorage.change_page(user_chat_id, 'chat')
    return True


def _limit_text(chat_data: dict, language_code: str) -> str:
    return post_limit.limit_text(chat_data.get('post_limit'), chat_data.get('post_limit_hours'), language_code)


async def show(params: ControllerParams):
    call, message = params['call'], params['message']
    language_code = params['language_code']

    if not len(params['state_data']):
        await raise_error(None, message, 'state_data_none')
        return

    # State data already have chat data
    if validate_typed_dict_interface(params['state_data'], ModeratedChatInterface, total=True):
        chat_data = params['state_data']
    else:
        chat_data = await Chat.find(params['state_data']['id'])

    if chat_data is None:
        await notify(call, message, localization.get_message(['chat', 'errors', 'not_found'], language_code))
        return False

    chat_info = await Chat.load_info(str(chat_data['service_id']))

    if 'error' in chat_info:
        await notify(call, message, localization.get_message(['chat', 'errors', 'not_found_tg'], language_code))
        return False

    paid = Tariff.is_paid(await Chat.owner_tariff_id(chat_data['id']))
    whitelist_count = await Chat.whitelist_data_count_provider(chat_data['id'])
    removed_week = await Chat.removed_count(chat_data['id'], 7)

    # Text: the group, its state, what the bot did, the rules in force
    message_text = localization.get_message(['chat', 'show', 'text'], language_code, chat_name=html.escape(
        chat_info['title']))
    if chat_info['nickname'] is not None:
        message_text += f" @{chat_info['nickname']}"

    if chat_data['disabled']:
        state_key = 'disabled'
    elif not chat_data['active']:
        state_key = 'paused'
    else:
        state_key = 'on'
    message_text += "\n\n" + localization.get_message(['chat', 'show', 'state', state_key], language_code)
    message_text += "\n" + localization.get_message(
        ['chat', 'show', 'who', 'everyone' if chat_data.get('everyone_can_write')
         else 'whitelist' if chat_data.get('allow_administrators', True) else 'whitelist_only'],
        language_code, count=whitelist_count)
    if chat_data.get('post_limit'):
        message_text += "\n" + localization.get_message(
            ['chat', 'show', 'limit_line'], language_code, limit=_limit_text(chat_data, language_code))
        if not paid:
            message_text += " " + localization.get_message(['chat', 'show', 'limit', 'paused_free'], language_code)
    message_text += "\n" + localization.get_message(
        ['chat', 'show', 'removed_week'], language_code, count=removed_week)
    if chat_data['disabled'] and await ChannelBonus.free_group_withheld(
            await User.get_id_by_service_id(message.chat.id)):
        message_text += "\n\n" + localization.get_message(['bonus', 'group_withheld'], language_code)
    elif chat_data['disabled']:
        message_text += "\n\n" + localization.get_message(['chat', 'show', 'disabled'], language_code)
    elif whitelist_count == 0 and not chat_data.get('everyone_can_write'):
        message_text += "\n\n" + localization.get_message(['chat', 'show', 'empty_whitelist_hint' if chat_data.get(
            'allow_administrators', True) else 'empty_whitelist_hint_strict'], language_code)
    elif paid and chat_data['active'] and outsiders_mode(chat_data) in ('silent', 'alert'):
        # The next step once someone may write: what the paid tariff (or the trial) is mostly for
        message_text += "\n\n" + localization.get_message(['chat', 'show', 'paid_entry_hint'], language_code)

    def button(path: list, callback_data: dict, **kwargs) -> dict:
        return {'text': localization.get_message(['chat', 'show', *path], language_code, **kwargs),
                'callback_data': callback_data}

    reply_markup = [
        [button(['add_to_whitelist_button'], {'tp': 'add_to_chat_whitelist'}),
         button(['whitelist_button'], {'tp': 'chat_whitelist'}, count=whitelist_count)],
        [button(['who_button', 'everyone' if chat_data.get('everyone_can_write') else 'whitelist'],
                {'tp': 'switch_mode'})],
        [button(['admins_button', 'free' if chat_data.get('allow_administrators', True) else 'checked'],
                {'tp': 'switch_admins'})],
        [button(['access_button', outsiders_mode(chat_data)], {'tp': 'chat_access'})],
        [{'text': ('' if paid else localization.get_message(['chat', 'show', 'locked'], language_code))
            + localization.get_message(['chat', 'show', 'limit_button'], language_code,
                                       limit=_limit_text(chat_data, language_code)),
          'callback_data': {'tp': 'chat_post_limit'}}],
        [button(['restriction_duration_button'], {'tp': 'chat_restriction_duration'},
                duration=chat_data.get('restriction_duration_minutes', 5))],
        [button(['active_button', 'active' if chat_data['active'] else 'inactive'], {'tp': 'switch_active'})],
        [button(['delete_button', 'deleting' if params['state_data'].get('deleting') else 'initial'],
                {'tp': 'delete'})],
    ]

    previous_id, next_id = await Chat.neighbours(chat_data['id'], message.chat.id)
    back_row = [go_back_inline_button(language_code)]
    if previous_id is not None:
        back_row = [{'text': '◀️', 'callback_data': {'tp': 'switch', 'id': previous_id}}, *back_row,
                    {'text': '▶️', 'callback_data': {'tp': 'switch', 'id': next_id}}]
    reply_markup.append(back_row)

    message_structures = [{
        'type': 'text',
        'text': message_text,
        'reply_markup': reply_markup,
        'parse_mode': 'HTML'
    }]
    await message_sender(message.chat.id, message_structures=message_structures)

    UserStorage.add_user_state_data(message.chat.id, 'chat', {**params['state_data'], **chat_data})


async def _refresh(params: ControllerParams, chat_data: dict | None):
    if chat_data is None:
        await raise_error(params['call'], params['message'], 'unexpected')
        return
    state = {key: value for key, value in params['state_data'].items() if key != 'deleting'}
    params['state_data'] = {**state, **dict(chat_data)}
    UserStorage.add_user_state_data(params['message'].chat.id, 'chat', params['state_data'])
    await show(params)


async def switch(params: ControllerParams):
    """◀️ ▶️: the user's previous or next group, without going back to the list."""
    call, message = params['call'], params['message']
    chat_id = params['state_data'].get('id')
    chat_data = await Chat.find(chat_id) if chat_id is not None else None
    if chat_data is None:
        await notify(call, message, localization.get_message(
            ['chat', 'errors', 'not_found'], params['language_code']), alert=True)
        return
    access = await Chat.validate_access(int(chat_data['service_id']), message.chat.id)
    if 'error' in access:
        await chat_access_denied(call, message, access)
        return
    params['state_data'] = {'id': chat_id}
    UserStorage.del_user_state_data(message.chat.id, 'chat')
    await _refresh(params, chat_data)


async def switch_mode(params: ControllerParams):
    """Who may write: the whitelist only, or everyone (then only the posting limit and the admins apply)."""
    current = params['state_data']
    everyone = not current.get('everyone_can_write', False)
    chat_data = await Chat.update_settings(current['id'], {'everyone_can_write': everyone})
    await notify(params['call'], params['message'], localization.get_message(
        ['chat', 'show', 'who_toast', 'everyone' if everyone else 'whitelist'], params['language_code']))
    await _refresh(params, chat_data)


async def switch_admins(params: ControllerParams):
    """Whether the group's owner and admins are checked like everyone (allow_administrators off): to try the bot
    on oneself, or for a group where admins must be on the whitelist too."""
    current = params['state_data']
    allowed = not current.get('allow_administrators', True)
    chat_data = await Chat.update_settings(current['id'], {'allow_administrators': allowed})
    await notify(params['call'], params['message'], localization.get_message(
        ['chat', 'show', 'admins_toast', 'free' if allowed else 'checked'], params['language_code']),
        alert=not allowed)
    await _refresh(params, chat_data)


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
