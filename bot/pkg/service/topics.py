"""Topics of a group with topics (a forum): in a protected topic the group's rules apply, in a free one the bot
leaves everyone alone.

Telegram gives bots no list of topics: the bot learns them from messages. A message in a topic (is_topic_message)
carries its thread id and, unless it replies to another message, the topic's first message with the topic's name
(reply_to_message.forum_topic_created). Messages of the general topic have no thread: it is thread 1 here, as in the
Bot API. A member can be muted only in the whole group, so where some topic is free the bot does not mute.

With MTProto keys (topic_lookup) the bot also asks Telegram about topics by id: the known ones get their name and
state as they are now (a rename the bot missed, a topic deleted), and the group's history is looked through for
topics nobody has written in since the bot came: a topic's id is the id of the message that created it, so the
ids from 2 up to the newest message are asked, a batch at a time, in the background. Telegram answers about every
id asked, calling the ones that are not topics deleted."""
import asyncio
import time

from aiogram.types import Message

from lib.language import localization
from pkg.repository import topic_repository
from pkg.service import topic_lookup
from pkg.system.logger import logger

GENERAL = 1
PER_PAGE = 10


def thread_of(message: Message) -> int | None:
    """The topic of a message in a group with topics; None in a group without (where a reply has a thread too)."""
    if not message.chat.is_forum:
        return None
    return message.message_thread_id if message.is_topic_message and message.message_thread_id else GENERAL


def name_from(message: Message) -> str | None:
    """The topic's name as it is now: told by "created" and "renamed"."""
    if message.forum_topic_created is not None:
        return message.forum_topic_created.name
    if message.forum_topic_edited is not None and message.forum_topic_edited.name:
        return message.forum_topic_edited.name
    return None


def name_hint_from(message: Message) -> str | None:
    """The name the topic was created with, from its first message attached to a message in it: it stays as it
    was after a rename, so it only names a topic the bot knows no name of."""
    root = message.reply_to_message
    if root is not None and root.forum_topic_created is not None and root.message_id == message.message_thread_id:
        return root.forum_topic_created.name
    return None


def closed_from(message: Message) -> bool | None:
    if message.forum_topic_closed is not None:
        return True
    if message.forum_topic_reopened is not None:
        return False
    return None


def is_service(message: Message) -> bool:
    return bool(message.forum_topic_created or message.forum_topic_edited or message.forum_topic_closed
                or message.forum_topic_reopened or message.general_forum_topic_hidden
                or message.general_forum_topic_unhidden)


async def seen(chat_id: int, message: Message) -> dict | None:
    """Remembers the topic of the message. None outside a group with topics; else whether the topic is protected,
    its name and whether the group has a free topic (has_free)."""
    thread = thread_of(message)
    if thread is None:
        return None
    return await topic_repository.seen(
        chat_id, thread, name_from(message), name_hint_from(message), closed_from(message))


def title(topic: dict, language_code: str | None) -> str:
    if topic['name']:
        return topic['name']
    if topic['thread_id'] == GENERAL:
        return localization.get_message(['chat', 'topics', 'general'], language_code)
    return localization.get_message(['chat', 'topics', 'unnamed'], language_code, id=topic['thread_id'])


# Looks through the history running now, by group id: one at a time per group
_scans: dict[int, asyncio.Task] = {}


def scanning(chat_id: int) -> bool:
    task = _scans.get(chat_id)
    return task is not None and not task.done()


async def _apply(chat: dict, found: list[dict]):
    """Telegram's answer about some ids: the topics kept as it says, the deleted ones (and ids that are no
    topics) gone."""
    for topic in found:
        if not topic['deleted']:
            # The general topic's name is the bot's own word for it, in the owner's language
            await topic_repository.found(
                chat['id'], topic['id'], None if topic['id'] == GENERAL else topic['title'], topic['closed'])
    await topic_repository.delete(chat['id'], [topic['id'] for topic in found if topic['deleted']])


async def refresh(chat: dict) -> int | None:
    """The general topic and the known ones as Telegram says they are now. The upper end for the look through the
    history (no smaller than the newest message id); None without MTProto or when it fails."""
    if not topic_lookup.available():
        return None
    service_id = int(chat['service_id'])
    ids = sorted({GENERAL, *await topic_repository.thread_ids(chat['id'])})
    for start in range(0, len(ids), topic_lookup.BATCH):
        found = await topic_lookup.by_ids(service_id, ids[start:start + topic_lookup.BATCH])
        if found is None:
            return None
        # Only a topic Telegram calls deleted goes: an id it leaves out keeps the owner's choice for it
        await _apply(chat, found)
    return max(await topic_lookup.newest(service_id) or 0, ids[-1])


async def _scan(chat: dict, newest: int):
    """Asks the ids from where the last look stopped up to `newest` and a batch past it (a topic made meanwhile);
    saves where it got after each batch."""
    service_id = int(chat['service_id'])
    upper = max(chat.get('topics_scan_upper') or 0, newest)
    scanned_to = max(chat.get('topics_scanned_to') or 1, 1)
    while scanned_to < upper + topic_lookup.BATCH:
        batch = list(range(scanned_to + 1, scanned_to + topic_lookup.BATCH + 1))
        found = await topic_lookup.by_ids(service_id, batch)
        if found is None:
            await topic_repository.save_scan(chat['id'], scanned_to, upper, False)
            return
        await _apply(chat, found)
        scanned_to = batch[-1]
        await topic_repository.save_scan(chat['id'], scanned_to, upper, False)
    await topic_repository.save_scan(chat['id'], scanned_to, upper, True)


# The list is shown as it is kept; Telegram is asked again in the background, at most once in this while unless
# the owner taps "Refresh"
FRESH_SECONDS = 60
# How long the topics page waits for an ask running (started by the group's page a moment before) to be done
WAIT_SECONDS = 3

# Asks running now, by group id; when each group was last asked and whether Telegram answered
_syncs: dict[int, asyncio.Task] = {}
_synced: dict[int, tuple[float, bool]] = {}


def sync_soon(chat: dict, force: bool = False) -> asyncio.Task | None:
    """Asks Telegram about the group's topics in the background (refresh, then the look through the history),
    unless an ask runs already or the last one is fresh. The ask running or started; None when nothing is asked."""
    if not topic_lookup.available():
        return None
    chat_id = chat['id']
    task = _syncs.get(chat_id)
    if task is not None and not task.done():
        return task
    last = _synced.get(chat_id)
    if not force and last is not None and last[1] and time.monotonic() - last[0] < FRESH_SECONDS:
        return None

    async def run():
        from pkg.service.chat import Chat

        try:
            newest = await refresh(chat)
        except Exception as e:
            logger.error('Topic refresh failed', chat_id, e)
            newest = None
        _synced[chat_id] = (time.monotonic(), newest is not None)
        if newest is not None:
            # The scan goes on from where the group says the last one stopped
            start_scan(await Chat.find(chat_id) or chat, newest)

    _syncs[chat_id] = asyncio.create_task(run())
    return _syncs[chat_id]


async def synced(chat: dict, force: bool = False, wait: float = WAIT_SECONDS) -> bool:
    """Asks Telegram (as `sync_soon`) and waits for the answer a little: whether the kept list is checked with
    Telegram. Without an answer yet it is what the last ask said; before any since the start, whether the group
    was ever looked through."""
    task = sync_soon(chat, force)
    if task is not None:
        await asyncio.wait({task}, timeout=wait)
    return checked(chat)


def checked(chat: dict) -> bool:
    """Whether the kept list is checked with Telegram, asking nothing."""
    if not topic_lookup.available():
        return False
    last = _synced.get(chat['id'])
    if last is not None:
        return last[1]
    return chat.get('topics_scan_upper') is not None


def forget():
    """Drops what is known of asks (tests)."""
    _syncs.clear()
    _synced.clear()


def start_scan(chat: dict, newest: int) -> bool:
    """Starts looking through the group's history in the background up to `newest` (from `refresh`), unless it
    runs already. False without MTProto."""
    if not topic_lookup.available():
        return False
    if scanning(chat['id']):
        return True

    async def run():
        try:
            await _scan(chat, newest)
        except Exception as e:
            logger.error('Topic scan failed', chat['id'], e)

    _scans[chat['id']] = asyncio.create_task(run())
    return True


def scan_progress(chat: dict) -> int | None:
    """How far the look through the history got, in percent; None when it has not started."""
    upper = chat.get('topics_scan_upper')
    if not upper:
        return None
    return min(100, int((chat.get('topics_scanned_to') or 1) * 100 / (upper + topic_lookup.BATCH)))
