"""Groups with topics: the bot learns the topics from messages, the group's rules apply in the protected ones, the
free ones are left alone, and the owner switches them on the topics page."""
import asyncio
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


# Names and states from Telegram itself (MTProto, faked here)

def _telegram_topics(bench: Bench, topics: dict[int, dict], newest: int | None = None,
                     gate: asyncio.Event | None = None) -> list[list[int]]:
    """MTProto answering as Telegram does (checked live): about every id asked, the ones that are not topics
    deleted; `newest` is the channel's pts; the look through the history (batches without the general topic)
    waits for `gate`. The asked batches."""
    from pkg.service import topic_lookup

    asked: list[list[int]] = []

    class Backend:
        async def by_ids(self, chat_service_id: int, ids: list[int]):
            assert chat_service_id == GROUP and len(ids) <= topic_lookup.BATCH
            asked.append(list(ids))
            if gate is not None and 1 not in ids:
                await gate.wait()
            return [{'id': i, 'deleted': False, 'closed': False, **topics[i]}
                    if i in topics and 'deleted' not in topics[i] else {'id': i, 'deleted': True} for i in ids]

        async def newest(self, chat_service_id: int):
            return newest

    _use_backend(bench, Backend())
    return asked


def _use_backend(bench: Bench, backend):
    from pkg.service import topic_lookup, topics

    topic_lookup.backend = backend
    bench.cleanups.append(lambda: setattr(topic_lookup, 'backend', None))
    bench.cleanups.append(topics.forget)


async def _scan_done(chat: dict):
    """Waits for Telegram's answer about the group's topics and the look through the history after it."""
    from pkg.service import topics
    for tasks in (topics._syncs, topics._scans):
        task = tasks.get(chat['id'])
        if task is not None:
            await task


async def test_name_hint_does_not_undo_a_rename(bench: Bench):
    """messages in a topic carry the name it was created with: after a rename the new name stays"""
    await _scene(bench)
    service = dict(text=None, forum=True, message_thread_id=12, is_topic_message=True)
    await bench.group_message(GROUP, OWNER, forum_topic_created={'name': 'Jobs', 'icon_color': 1}, **service)
    await bench.group_message(GROUP, OWNER, forum_topic_edited={'name': 'Work'}, **service)
    await _in_topic(bench, ALICE, 12, 'Jobs')
    assert (await _topics(bench))[12]['name'] == 'Work'


async def test_history_looked_through_for_topics(bench: Bench):
    """with MTProto the topics page asks Telegram about the group's history: topics nobody wrote in since the bot
    came show up with their names, closed ones marked, up to the newest message (the channel's pts) and a batch
    past it"""
    chat = await _scene(bench)
    asked = _telegram_topics(bench, {
        1: {'title': 'General'},
        40: {'title': 'Rent'},
        180: {'title': 'Jobs', 'closed': True},
        330: {'title': 'Late'},
    }, newest=340, gate=(gate := asyncio.Event()))
    await _open_group_page(bench, chat)
    await bench.tap(OWNER, json.dumps({'tp': 'chat_topics'}))
    assert 'Ищу разделы в истории группы' in _shown(bench).text, _shown(bench).text
    gate.set()
    await _scan_done(chat)

    assert await _topics(bench) == {
        1: {'thread_id': 1, 'name': None, 'protected': True, 'closed': False},
        40: {'thread_id': 40, 'name': 'Rent', 'protected': True, 'closed': False},
        180: {'thread_id': 180, 'name': 'Jobs', 'protected': True, 'closed': True},
        330: {'thread_id': 330, 'name': 'Late', 'protected': True, 'closed': False},
    }
    looked = sorted(i for batch in asked[1:] for i in batch)
    assert looked == list(range(2, 502)), (looked[0], looked[-1])  # batches of 100 past 340 + 100

    await bench.tap(OWNER, json.dumps({'tp': 'tpc_page', 'p': 1}))
    page = _shown(bench)
    assert 'Список сверен с Telegram' in page.text, page.text
    texts = [b['text'] for b in _buttons(page)]
    assert texts[:4] == ['🛡 Общий', '🛡 Rent', '🛡 Late', '🛡 🔒 Jobs'], texts


async def test_known_topics_renamed_and_deleted_from_telegram(bench: Bench):
    """a rename the bot missed and a deleted topic: the topics page takes them from Telegram; the owner's choice
    for the others stays"""
    chat = await _scene(bench)
    await _in_topic(bench, ALICE, 4, 'Old')
    await _in_topic(bench, ALICE, 9, 'Gone')
    await _in_topic(bench, ALICE, 15, 'Quiet')
    await bench.sql('UPDATE chat_topics SET protected = false WHERE thread_id = 15')
    _telegram_topics(bench, {1: {'title': 'General'}, 4: {'title': 'New'}, 9: {'deleted': True},
                             15: {'title': 'Quiet'}}, newest=20)
    await _open_group_page(bench, chat)
    await bench.tap(OWNER, json.dumps({'tp': 'chat_topics'}))
    await _scan_done(chat)
    rows = await _topics(bench)
    assert rows[4]['name'] == 'New' and 9 not in rows and rows[15]['protected'] is False, rows


async def test_without_telegram_s_answer_the_page_is_as_before(bench: Bench):
    """MTProto on but failing: the page lists what the bot has seen and says how to add the rest"""
    chat = await _scene(bench)
    await _in_topic(bench, ALICE, 4, 'Services')

    class Failing:
        async def by_ids(self, chat_service_id: int, ids: list[int]):
            return None

        async def newest(self, chat_service_id: int):
            return None

    _use_backend(bench, Failing())
    await _open_group_page(bench, chat)
    await bench.tap(OWNER, json.dumps({'tp': 'chat_topics'}))
    page = _shown(bench)
    assert 'Нужного нет?' in page.text and 'Ищу разделы' not in page.text, page.text
    assert '🛡 Services' in [b['text'] for b in _buttons(page)]


async def test_telegram_asked_when_the_group_page_opens(bench: Bench):
    """the group's page asks Telegram about the topics in the background: the topics page opened next shows the
    answer without asking again; opened again within a minute it asks nothing, "Refresh" asks always"""
    chat = await _scene(bench)
    await _in_topic(bench, ALICE, 4, 'Old')
    await _in_topic(bench, ALICE, 16, 'Kekes')
    asked = _telegram_topics(bench, {1: {'title': 'General'}, 4: {'title': 'New'}}, newest=20)
    await _open_group_page(bench, chat)
    assert asked and asked[0] == [1, 4, 16], asked
    await _scan_done(chat)
    count = len(asked)

    await bench.tap(OWNER, json.dumps({'tp': 'chat_topics'}))
    page = _shown(bench)
    assert len(asked) == count, 'the answer got by the group page is used'
    texts = [b['text'] for b in _buttons(page)]
    assert '🛡 New' in texts and not any('Kekes' in text for text in texts), texts
    assert 'Список сверен с Telegram' in page.text, page.text

    await bench.tap(OWNER, json.dumps({'tp': 'tpc_page', 'p': 1}))
    assert len(asked) == count, 'a page turned within a minute asks nothing'
    await bench.tap(OWNER, json.dumps({'tp': 'tpc_page', 'p': 1, 'r': 1}))
    await _scan_done(chat)
    assert len(asked) > count and asked[count] == [1, 4], asked
