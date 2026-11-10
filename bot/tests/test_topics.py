"""Groups with topics: the bot learns the topics from messages, the group's rules apply in the protected ones, the
free ones are left alone, and the owner switches them on the topics page."""
import json

from tests.bench import Bench, person

GROUP = -1001000000001
OWNER = person(501, 'owner', 'ru')
ALICE = person(601, 'Alice')
STRANGER = person(701, 'stranger', 'en')
ANONYMOUS_ADMIN = {**person(1087968824, 'GroupAnonymousBot'), 'is_bot': True}


async def _scene(bench: Bench, **chat_fields) -> dict:
    owner = await bench.owner(OWNER)
    chat = await bench.group(GROUP, owner, **chat_fields)
    bench.telegram.chats[GROUP]['is_forum'] = True
    await bench.whitelist(chat, 'Alice')
    return chat


async def _in_topic(bench: Bench, user: dict, thread: int, name: str | None = 'Services', text: str | None = 'hi',
                    **extra) -> dict:
    """A message in a topic: unless it replies to another one, Telegram attaches the topic's first message."""
    root = {} if name is None else {'reply_to_message': {
        'message_id': thread, 'date': 0, 'chat': {'id': GROUP, 'type': 'supergroup', 'is_forum': True},
        'from': OWNER, 'message_thread_id': thread, 'forum_topic_created': {'name': name, 'icon_color': 7322096}}}
    return await bench.group_message(GROUP, user, text, forum=True, message_thread_id=thread, is_topic_message=True,
                                     **{**root, **extra})


async def _topics(bench: Bench) -> dict[int, dict]:
    return {row['thread_id']: dict(row) for row in await bench.sql(
        'SELECT thread_id, name, protected, closed FROM chat_topics')}


def _deleted(bench: Bench) -> int:
    return len(bench.telegram.calls_of('deleteMessage'))


# What the bot does in the group

async def test_topic_learned_with_its_name_and_protected(bench: Bench):
    """a message in a topic: the bot remembers the topic with its name, protected; a stranger's message there goes"""
    await _scene(bench)
    await _in_topic(bench, ALICE, 4)
    await _in_topic(bench, STRANGER, 4)
    assert await _topics(bench) == {4: {'thread_id': 4, 'name': 'Services', 'protected': True, 'closed': False}}
    assert _deleted(bench) == 1
    assert len(bench.telegram.calls_of('restrictChatMember')) == 1, 'all topics protected: the usual mute'
    [notice] = bench.telegram.sent_to(GROUP)
    assert 'open to everyone' not in notice.text


async def test_free_topic_left_alone(bench: Bench):
    """in a free topic a stranger writes and nothing happens"""
    await _scene(bench)
    await _in_topic(bench, ALICE, 4)
    await bench.sql('UPDATE chat_topics SET protected = false')
    bench.telegram.calls.clear()
    await _in_topic(bench, STRANGER, 4)
    assert not bench.telegram.calls_of('deleteMessage', 'restrictChatMember', 'sendMessage'), bench.telegram.calls


async def test_no_mute_while_a_topic_is_free(bench: Bench):
    """with a free topic in the group a stranger's message in a protected one goes, but nobody is muted: a mute
    would keep them out of the free topic too"""
    await _scene(bench)
    await _in_topic(bench, ALICE, 4, 'Ads')
    await bench.sql('UPDATE chat_topics SET protected = false')
    await _in_topic(bench, STRANGER, 6, 'Services')
    assert _deleted(bench) == 1
    assert not bench.telegram.calls_of('restrictChatMember')
    [notice] = bench.telegram.sent_to(GROUP)
    assert notice.message_thread_id == 6
    assert 'Some topics of this group are open to everyone' in notice.text, notice.text


async def test_new_topics_free_by_the_owner_s_choice(bench: Bench):
    """the owner made new topics free: a topic the bot sees first is free, the stranger's message stays"""
    await _scene(bench, topics_default_protected=False)
    await _in_topic(bench, STRANGER, 9, 'Flood')
    assert not bench.telegram.calls_of('deleteMessage')
    assert (await _topics(bench))[9]['protected'] is False


async def test_general_topic_is_thread_one(bench: Bench):
    """a message in the general topic has no thread: the bot keeps it as topic 1, without a name"""
    await _scene(bench)
    await bench.group_message(GROUP, STRANGER, forum=True)
    assert await _topics(bench) == {1: {'thread_id': 1, 'name': None, 'protected': True, 'closed': False}}
    assert _deleted(bench) == 1


async def test_topic_service_messages_tell_name_and_state(bench: Bench):
    """created by an anonymous admin, renamed, closed, reopened: the bot keeps the name and the state and removes
    none of these messages"""
    await _scene(bench)
    service = dict(text=None, forum=True, message_thread_id=12, is_topic_message=True)
    await bench.group_message(GROUP, ANONYMOUS_ADMIN, forum_topic_created={'name': 'Jobs', 'icon_color': 1}, **service)
    assert (await _topics(bench))[12]['name'] == 'Jobs'
    await bench.group_message(GROUP, STRANGER, forum_topic_edited={'name': 'Work'}, **service)
    await bench.group_message(GROUP, STRANGER, forum_topic_edited={'icon_custom_emoji_id': '5'}, **service)
    assert (await _topics(bench))[12]['name'] == 'Work', 'an icon changed alone keeps the name'
    await bench.group_message(GROUP, STRANGER, forum_topic_closed={}, **service)
    assert (await _topics(bench))[12]['closed'] is True
    await bench.group_message(GROUP, STRANGER, forum_topic_reopened={}, **service)
    assert (await _topics(bench))[12]['closed'] is False
    assert not bench.telegram.calls_of('deleteMessage')


async def test_reply_in_a_topic_keeps_the_name(bench: Bench):
    """a reply inside a topic carries the replied message, not the topic's first one: the name stays as it was"""
    await _scene(bench)
    await _in_topic(bench, ALICE, 4, 'Services')
    await _in_topic(bench, ALICE, 4, name=None, reply_to_message={
        'message_id': 50, 'date': 0, 'chat': {'id': GROUP, 'type': 'supergroup'}, 'from': ALICE, 'text': 'x'})
    assert (await _topics(bench))[4]['name'] == 'Services'


async def test_paused_group_still_learns_topics(bench: Bench):
    """a paused group is not moderated, but its topics are remembered for the topics page"""
    await _scene(bench, active=False)
    await _in_topic(bench, STRANGER, 4)
    assert 4 in await _topics(bench)
    assert not bench.telegram.calls_of('deleteMessage')


async def test_group_without_topics_keeps_no_topics(bench: Bench):
    """a reply in a group without topics carries a thread, but it is not a topic"""
    owner = await bench.owner(OWNER)
    await bench.group(GROUP, owner)
    await bench.group_message(GROUP, STRANGER, message_thread_id=5)
    assert await _topics(bench) == {}
    assert _deleted(bench) == 1 and len(bench.telegram.calls_of('restrictChatMember')) == 1


async def test_owner_alert_names_the_topic(bench: Bench):
    """the owner's alert about a deleted message says in which topic it was"""
    await _scene(bench)
    await _in_topic(bench, STRANGER, 4, 'Services')
    [alert] = [call for call in bench.telegram.sent_to(OWNER['id']) if call.reply_markup]
    assert 'Group' in alert.text and '› Services' in alert.text, alert.text


# The topics page

def _buttons(call) -> list[dict]:
    rows = getattr(call.reply_markup, 'inline_keyboard', None) or []
    return [{'text': b.text, 'data': json.loads(b.callback_data) if b.callback_data else None}
            for row in rows for b in row]


def _shown(bench: Bench):
    return [call for call in bench.telegram.calls_of('sendMessage', 'editMessageText')
            if int(call.chat_id or 0) == OWNER['id']][-1]


async def _open_group_page(bench: Bench, chat: dict):
    await bench.private_message(OWNER, f"/start chat_{chat['id']}")
    return _shown(bench)


async def test_group_page_shows_topics(bench: Bench):
    """the page of a group with topics has the topics line and button; a group without topics has neither"""
    chat = await _scene(bench)
    page = await _open_group_page(bench, chat)
    assert '🗂 Разделы' in [b['text'] for b in _buttons(page)]
    assert 'Разделы под защитой' not in page.text, 'no topics seen yet: no line'
    await _in_topic(bench, ALICE, 4)
    page = await _open_group_page(bench, chat)
    assert 'Разделы под защитой: 1 из 1' in page.text, page.text

    bench.telegram.chats[GROUP].pop('is_forum')
    page = await _open_group_page(bench, chat)
    assert '🗂 Разделы' not in [b['text'] for b in _buttons(page)]


async def test_topics_page_empty_then_listed_and_switched(bench: Bench):
    """with no topics seen the page says how to make them show up; then it lists them, a tap switches one,
    the mute note appears with a free topic, and the setting for new topics switches"""
    chat = await _scene(bench)
    await _open_group_page(bench, chat)
    await bench.tap(OWNER, json.dumps({'tp': 'chat_topics'}))
    assert 'Бот ещё не видел сообщений в разделах' in _shown(bench).text, _shown(bench).text

    await _in_topic(bench, ALICE, 4, 'Services')
    await bench.group_message(GROUP, ALICE, forum=True)
    await bench.tap(OWNER, json.dumps({'tp': 'tpc_page', 'p': 1}))
    page = _shown(bench)
    assert 'Под защитой: 2 из 2' in page.text and 'не даёт мут' not in page.text, page.text
    texts = [b['text'] for b in _buttons(page)]
    assert texts[:2] == ['🛡 Общий', '🛡 Services'], texts
    assert 'Новые разделы: 🛡 под защитой' in texts

    await bench.tap(OWNER, json.dumps({'tp': 'tpc_set', 't': 4, 'p': 1}))
    assert (await _topics(bench))[4]['protected'] is False
    assert bench.telegram.calls_of('answerCallbackQuery')[-1].text == 'Services: 💬 свободный'
    page = _shown(bench)
    assert '💬 Services' in [b['text'] for b in _buttons(page)] and 'не даёт мут' in page.text, page.text

    await bench.tap(OWNER, json.dumps({'tp': 'tpc_def', 'p': 1}))
    [row] = await bench.sql('SELECT topics_default_protected FROM moderated_chats')
    assert row['topics_default_protected'] is False
    assert 'Новые разделы: 💬 свободные' in [b['text'] for b in _buttons(_shown(bench))]


async def test_topics_page_pages(bench: Bench):
    """more than ten topics go on pages"""
    chat = await _scene(bench)
    for thread in range(2, 15):
        await _in_topic(bench, ALICE, thread, f'T{thread}')
    await _open_group_page(bench, chat)
    await bench.tap(OWNER, json.dumps({'tp': 'chat_topics'}))
    texts = [b['text'] for b in _buttons(_shown(bench))]
    assert '1/2' in texts and '🛡 T2' in texts and '🛡 T14' not in texts, texts
    await bench.tap(OWNER, json.dumps({'tp': 'tpc_page', 'p': 2}))
    texts = [b['text'] for b in _buttons(_shown(bench))]
    assert '2/2' in texts and '🛡 T14' in texts, texts
