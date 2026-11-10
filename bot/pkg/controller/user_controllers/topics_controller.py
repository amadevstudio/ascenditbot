"""The topics page under the page of a group with topics: each topic the bot has seen, protected (the group's rules
apply) or free (the bot leaves it alone), switched by a tap; and whether topics the bot sees later are protected.
On every tariff."""
import html

from framework.controller import state_data
from framework.controller.message_tools import go_back_inline_button, message_sender, notify
from framework.controller.types import ControllerParams
from lib.language import localization
from pkg.controller.user_controllers.common_controller import raise_error
from pkg.repository import topic_repository
from pkg.service import topics
from pkg.service.chat import Chat


def _text(path: list, language_code: str | None, **kwargs) -> str:
    return localization.get_message(['chat', 'topics', *path], language_code, **kwargs)


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


def mark(protected: bool) -> str:
    return '🛡' if protected else '💬'


async def _render(params: ControllerParams, chat: dict, page: int = 1):
    language_code = params['language_code']
    counts = await topic_repository.counts(chat['id'])
    total = counts['total'] if counts else 0
    pages = max(1, -(-total // topics.PER_PAGE))
    page = min(max(1, page), pages)
    rows = await topic_repository.of_chat(chat['id'], topics.PER_PAGE, (page - 1) * topics.PER_PAGE)

    lines = [_text(['text'], language_code, chat_name=html.escape(await Chat.name_of(chat)))]
    if total:
        lines.append(_text(['legend'], language_code))
        lines.append(_text(['count'], language_code, protected=counts['protected'], total=total))
        free = total - counts['protected'] or not chat.get('topics_default_protected', True)
        if free and chat.get('restriction_duration_minutes', 5) > 0:
            lines.append(_text(['no_mute'], language_code))
        lines.append(_text(['missing'], language_code))
    else:
        lines.append(_text(['empty'], language_code))

    reply_markup = [[{
        'text': f"{mark(row['protected'])} {'🔒 ' if row['closed'] else ''}"
                f"{topics.title(row, language_code)}",
        'callback_data': {'tp': 'tpc_set', 't': row['thread_id'], 'p': page}}] for row in rows]
    if pages > 1:
        reply_markup.append([
            {'text': '◀️', 'callback_data': {'tp': 'tpc_page', 'p': page - 1 if page > 1 else pages}},
            {'text': f'{page}/{pages}', 'callback_data': {'tp': 'tpc_page', 'p': page}},
            {'text': '▶️', 'callback_data': {'tp': 'tpc_page', 'p': page + 1 if page < pages else 1}}])
    default = chat.get('topics_default_protected', True)
    reply_markup.append([{'text': _text(['default_button', 'protected' if default else 'free'], language_code),
                          'callback_data': {'tp': 'tpc_def', 'p': page}}])
    reply_markup.append([{'text': _text(['refresh_button'], language_code),
                          'callback_data': {'tp': 'tpc_page', 'p': page}}])
    reply_markup.append([go_back_inline_button(language_code)])
    await message_sender(params['message'].chat.id, message_structures=[{
        'type': 'text', 'text': "\n\n".join(lines), 'reply_markup': reply_markup, 'parse_mode': 'HTML'}])


def _page_of(params: ControllerParams) -> int:
    try:
        return int((params['state_data'] or {}).get('p') or 1)
    except (TypeError, ValueError):
        return 1


async def page(params: ControllerParams):
    chat = await _chat(params)
    if chat is None:
        return False
    await _render(params, chat, _page_of(params))


async def turn_page(params: ControllerParams):
    """Another page of topics, or the same one again to see topics the bot has seen since."""
    chat = await _chat(params)
    if chat is None:
        return
    if params['call'] is not None:
        await params['call'].answer()
    await _render(params, chat, _page_of(params))


async def toggle(params: ControllerParams):
    chat = await _chat(params)
    if chat is None:
        return
    try:
        thread_id = int((params['state_data'] or {}).get('t'))
    except (TypeError, ValueError):
        return
    topic = await topic_repository.toggle(chat['id'], thread_id)
    if topic is not None:
        language_code = params['language_code']
        await notify(params['call'], params['message'], _text(
            ['toggled', 'protected' if topic['protected'] else 'free'], language_code,
            topic=topics.title(topic, language_code)))
    await _render(params, chat, _page_of(params))


async def toggle_default(params: ControllerParams):
    chat = await _chat(params)
    if chat is None:
        return
    protected = not chat.get('topics_default_protected', True)
    await topic_repository.set_default(chat['id'], protected)
    chat = await Chat.find(chat['id'])
    await notify(params['call'], params['message'], _text(
        ['default_toast', 'protected' if protected else 'free'], params['language_code']))
    await _render(params, chat, _page_of(params))
