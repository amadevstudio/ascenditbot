"""Topics of a group with topics (a forum): in a protected topic the group's rules apply, in a free one the bot
leaves everyone alone.

Telegram gives bots no list of topics: the bot learns them from messages. A message in a topic (is_topic_message)
carries its thread id and, unless it replies to another message, the topic's first message with the topic's name
(reply_to_message.forum_topic_created). Messages of the general topic have no thread: it is thread 1 here, as in the
Bot API. A member can be muted only in the whole group, so where some topic is free the bot does not mute."""
from aiogram.types import Message

from lib.language import localization
from pkg.repository import topic_repository

GENERAL = 1
PER_PAGE = 10


def thread_of(message: Message) -> int | None:
    """The topic of a message in a group with topics; None in a group without (where a reply has a thread too)."""
    if not message.chat.is_forum:
        return None
    return message.message_thread_id if message.is_topic_message and message.message_thread_id else GENERAL


def name_from(message: Message) -> str | None:
    if message.forum_topic_created is not None:
        return message.forum_topic_created.name
    if message.forum_topic_edited is not None and message.forum_topic_edited.name:
        return message.forum_topic_edited.name
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
    return await topic_repository.seen(chat_id, thread, name_from(message), closed_from(message))


def title(topic: dict, language_code: str | None) -> str:
    if topic['name']:
        return topic['name']
    if topic['thread_id'] == GENERAL:
        return localization.get_message(['chat', 'topics', 'general'], language_code)
    return localization.get_message(['chat', 'topics', 'unnamed'], language_code, id=topic['thread_id'])
