"""The posting limit page under the group's page: the usual limits as buttons, or the owner's own typed in words
("3 в час", "10 за 2 дня", "выкл"). Set on any tariff, applied on a paid one."""
import html

from framework.controller import state_data
from framework.controller.message_tools import go_back_inline_button, message_sender, notify
from framework.controller.types import ControllerParams
from lib.language import localization
from pkg.controller.user_controllers.common_controller import raise_error
from pkg.service import post_limit
from pkg.service.chat import Chat
from pkg.service.tariff import Tariff
from pkg.service.user_storage import UserStorage


def _text(path: list, language_code: str | None, **kwargs) -> str:
    return localization.get_message(['chat', 'post_limit', *path], language_code, **kwargs)


async def _chat(params: ControllerParams) -> dict | None:
    chat_state = state_data.get_local_state_data(params['message'], 'chat')
    if not chat_state or 'id' not in chat_state:
        await raise_error(None, params['message'], 'state_data_none')
        return None
    chat = await Chat.find(chat_state['id'])
    if chat is None:
        await notify(params['call'], params['message'], localization.get_message(
            ['chat', 'errors', 'not_found'], params['language_code']))
    return chat


async def _render(params: ControllerParams, chat: dict, notice: str | None = None):
    language_code = params['language_code']
    current = post_limit.of_chat(chat)
    lines = [_text(['text'], language_code, chat_name=html.escape(await Chat.name_of(chat)),
                   limit=post_limit.limit_text(*(current or (None, None)), language_code))]
    if not Tariff.is_paid(await Chat.owner_tariff_id(chat['id'])):
        lines.append(_text(['free'], language_code))
    if notice:
        lines.insert(0, notice)

    def button(choice: tuple[int, int] | None) -> dict:
        label = (post_limit.limit_text(*choice, language_code) if choice
                 else _text(['off_button'], language_code))
        mark = '• ' if choice == current else ''
        count, hours = choice or (0, 0)
        return {'text': mark + label, 'callback_data': {'tp': 'lim_set', 'n': count, 'h': hours}}

    choices = [None, *post_limit.CHOICES]
    rows = [[button(choice) for choice in choices[i:i + 2]] for i in range(0, len(choices), 2)]
    rows.append([go_back_inline_button(language_code)])
    await message_sender(params['message'].chat.id, message_structures=[{
        'type': 'text', 'text': "\n\n".join(lines), 'reply_markup': rows, 'parse_mode': 'HTML'}])


async def _save(params: ControllerParams, chat: dict, choice: tuple[int, int] | None) -> dict:
    chat = await Chat.update_settings(chat['id'], {
        'post_limit': choice[0] if choice else None, 'post_limit_hours': choice[1] if choice else None})
    # The group's page shows the new limit when the owner goes back
    chat_state = state_data.get_local_state_data(params['message'], 'chat') or {}
    UserStorage.add_user_state_data(params['message'].chat.id, 'chat', {
        **chat_state, 'post_limit': chat['post_limit'], 'post_limit_hours': chat['post_limit_hours']})
    return chat


async def page(params: ControllerParams):
    call, message = params['call'], params['message']
    chat = await _chat(params)
    if chat is None:
        return False
    language_code = params['language_code']

    # A limit typed in words
    if call is None and message.text is not None and not message.text.startswith('/'):
        parsed = post_limit.parse_limit(message.text)
        if parsed is None:
            await _render(params, chat, notice=_text(['invalid'], language_code, text=html.escape(
                message.text.strip()[:50]), max_count=post_limit.MAX_COUNT))
            return
        choice = None if parsed == post_limit.OFF else parsed
        chat = await _save(params, chat, choice)
        await _render(params, chat, notice=_text(['saved'], language_code, limit=post_limit.limit_text(
            *(choice or (None, None)), language_code)))
        return

    await _render(params, chat)


async def set_limit(params: ControllerParams):
    """One of the buttons: n posts in h hours, or none (n 0)."""
    chat = await _chat(params)
    if chat is None:
        return
    data = params['state_data'] or {}
    count, hours = int(data.get('n') or 0), int(data.get('h') or 0)
    choice = (count, hours) if count and hours else None
    if choice is not None and (count > post_limit.MAX_COUNT or hours > post_limit.MAX_HOURS):
        return
    chat = await _save(params, chat, choice)
    await notify(params['call'], params['message'], localization.get_message(
        ['chat', 'post_limit', 'saved'], params['language_code'],
        limit=post_limit.limit_text(*(choice or (None, None)), params['language_code'])).replace('✅ ', ''))
    await _render(params, chat)
