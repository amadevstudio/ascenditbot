"""MTProto for what the Bot API does not give bots: the topics of a group by their ids (messages.getForumTopicsByID,
the one topic method open to bots; the list of topics, messages.getForumTopics, is for users only).

The bot logs in to MTProto with its own token, without updates (aiogram keeps getting them through the Bot API).
It needs TELEGRAM_API_ID and TELEGRAM_API_HASH (my.telegram.org); without them `available()` is False and the bot
knows topics from messages only. The session is kept in Redis, so a restart does not log in again."""
import asyncio

from framework.repository.storage_connection import Storage
from pkg.config.config import environment
from pkg.system.logger import logger

# Ids asked in one request
BATCH = 100
_SESSION_KEY = 'mtproto:bot_session'

_client = None
_client_lock = asyncio.Lock()
_peers: dict[int, object] = {}

# Tests put a fake here: an object with async `by_ids(chat_service_id, ids)` and `newest(chat_service_id)`,
# answering as those below do
backend = None


def available() -> bool:
    return backend is not None or bool(environment.get('TELEGRAM_API_ID') and environment.get('TELEGRAM_API_HASH'))


async def _get_client():
    global _client
    async with _client_lock:
        if _client is not None and _client.is_connected():
            return _client
        from telethon import TelegramClient
        from telethon.sessions import StringSession

        storage = Storage().connection
        saved = storage.get(_SESSION_KEY)
        client = TelegramClient(
            StringSession(saved.decode() if saved else None), int(environment['TELEGRAM_API_ID']),
            environment['TELEGRAM_API_HASH'], receive_updates=False, flood_sleep_threshold=30)
        await client.start(bot_token=environment['TELEGRAM_BOT_TOKEN'])
        storage.set(_SESSION_KEY, client.session.save())
        _client = client
        return client


async def _peer(client, chat_service_id: int):
    """The group as MTProto wants it: a channel id without -100 and its access hash, which a bot may ask with 0
    (checked live)."""
    if chat_service_id in _peers:
        return _peers[chat_service_id]
    from telethon.tl.functions.channels import GetChannelsRequest
    from telethon.tl.types import InputChannel, InputPeerChannel

    channel_id = -int(chat_service_id) - 1_000_000_000_000
    result = await client(GetChannelsRequest([InputChannel(channel_id, 0)]))
    channel = result.chats[0]
    _peers[chat_service_id] = InputPeerChannel(channel.id, channel.access_hash)
    return _peers[chat_service_id]


async def newest(chat_service_id: int) -> int | None:
    """No smaller than the id of the group's newest message: the channel's pts (every new message adds one to both,
    edits and deletions add to pts only; a bot is not given the newest message itself, and top_message of a topic
    comes to a bot as 0). None when MTProto is off or fails (logged)."""
    if not available():
        return None
    if backend is not None:
        return await backend.newest(chat_service_id)
    try:
        from telethon.tl.functions.channels import GetFullChannelRequest
        from telethon.tl.types import InputChannel

        client = await _get_client()
        peer = await _peer(client, chat_service_id)
        result = await client(GetFullChannelRequest(InputChannel(peer.channel_id, peer.access_hash)))
    except Exception as e:
        logger.warning('MTProto full channel failed', chat_service_id, type(e).__name__, e)
        return None
    return result.full_chat.pts


async def by_ids(chat_service_id: int, ids: list[int]) -> list[dict] | None:
    """Telegram's answer about `ids` (at most BATCH): {'id', 'deleted'} and, unless deleted, 'title', 'closed'.
    Telegram answers about every id it is asked: an id that is not a topic (any other message, or no message yet)
    comes back deleted, as a deleted topic does. None when MTProto is off or fails (logged): the caller goes on
    without it."""
    if not ids or not available():
        return None
    if backend is not None:
        return await backend.by_ids(chat_service_id, ids)
    try:
        from telethon.tl.functions.messages import GetForumTopicsByIDRequest
        from telethon.tl.types import ForumTopicDeleted

        client = await _get_client()
        result = await client(GetForumTopicsByIDRequest(peer=await _peer(client, chat_service_id), topics=ids))
    except Exception as e:
        logger.warning('MTProto topics by id failed', chat_service_id, type(e).__name__, e)
        return None
    topics = []
    for topic in result.topics:
        if isinstance(topic, ForumTopicDeleted):
            topics.append({'id': topic.id, 'deleted': True})
        else:
            topics.append({'id': topic.id, 'deleted': False, 'title': topic.title, 'closed': bool(topic.closed)})
    return topics
