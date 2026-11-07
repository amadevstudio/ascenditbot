import datetime
import time

from aiogram.types import EphemeralMessageParameters

from framework.system import telegram_types, telegram_exceptions
from framework.system.bot_setup import bot
from lib.language import localization
from pkg.repository import allowed_user_repository, chat_repository
from pkg.service import access
from pkg.service.chat import Chat
from pkg.service.allowed_user import full_name
from pkg.service.member_alerts import MemberAlerts
from pkg.service import post_limit
from pkg.service.post_limit import PostLimit
from pkg.service.tariff import Tariff
from pkg.system.logger import logger

# One notice per member per chat at most this often, so a flood of messages does not become a flood of notices
_NOTICE_INTERVAL_SECONDS = 600
_last_notice: dict[tuple[int, int, str], float] = {}
_TELEGRAM_SERVICE_ID = 777000


async def incoming_chat_message(message: telegram_types.Message, edited: bool = False):
    """A new message in a group, or an edit of an old one (edited): an edit by someone who may not write now (an
    access that has ended, an outsider's old message) goes as a new message would, but without the mute, the
    owner's alert and the posting limit: it is not a new post."""
    if message.from_user is None:
        logger.warning("Incoming chat message has no sender")
        return

    # Messages of bots, of anonymous admins (GroupAnonymousBot), of members writing as a channel (Channel_Bot)
    # and the posts a linked channel forwards to its discussion group (sent by 777000, "Telegram") stay
    if message.from_user.is_bot or message.is_automatic_forward or message.from_user.id == _TELEGRAM_SERVICE_ID:
        return

    # Service messages (joins, pins, a new title) are Telegram's, not the member's
    if message.new_chat_members or message.left_chat_member or message.pinned_message \
            or message.new_chat_title or message.new_chat_photo or message.delete_chat_photo:
        return

    chat_service_id: int = message.chat.id
    sender = message.from_user

    # Validate chat: unknown, over the tariff limit, or paused by the owner
    chat_data = await Chat.find_by({'service_id': str(chat_service_id)})
    if chat_data is None or chat_data['disabled'] or not chat_data['active']:
        return

    privileges = await allowed_user_repository.get_privileges(
        str(chat_service_id), str(sender.id), sender.username)
    whitelisted = privileges is not None and privileges['active']
    if privileges is not None:
        await allowed_user_repository.remember_member(
            privileges['id'], str(sender.id), sender.username, full_name(sender))

    allowed = whitelisted or chat_data.get('everyone_can_write', False)
    is_admin = None

    # The owner and the admins write without being on the whitelist (moderated_chats.allow_administrators)
    if not allowed and chat_data.get('allow_administrators', True):
        is_admin = await Chat.is_administrator(chat_service_id, sender.id)
        allowed = is_admin

    if not allowed:
        if not await _remove(message):
            return
        await chat_repository.count_removed(chat_data['id'])
        if edited:
            await notify_removed(message, chat_data['id'])
            return
        await Chat.restrict_user(
            chat_service_id, sender.id, chat_data.get('restriction_duration_minutes', 5), message.chat.type,
            is_admin=is_admin)
        await notify_removed(message, chat_data['id'])
        await MemberAlerts.removed(chat_data, message)
        return

    if not edited:
        await _apply_post_limit(message, chat_data, is_admin)


async def _apply_post_limit(message: telegram_types.Message, chat_data: dict, is_admin: bool | None):
    """A member over the group's posting limit loses the post and is told when the next one is possible.
    The limit is a paid setting: it is not applied while the owner is on the free tariff."""
    limit = post_limit.of_chat(chat_data)
    if limit is None:
        return
    if is_admin is None and chat_data.get('allow_administrators', True):
        is_admin = await Chat.is_administrator(message.chat.id, message.from_user.id)
    if is_admin:
        return
    if not Tariff.is_paid(await Chat.owner_tariff_id(chat_data['id'])):
        return

    next_at = PostLimit.take(message.chat.id, message.from_user.id, *limit)
    if next_at is None:
        return
    if not await _remove(message):
        return
    await chat_repository.count_removed(chat_data['id'])
    await notify_over_limit(message, limit, next_at)


async def _remove(message: telegram_types.Message) -> bool:
    try:
        await message.delete()
        return True
    except telegram_exceptions.TelegramForbiddenError as e:
        logger.warning(e)
    except telegram_exceptions.TelegramBadRequest as e:
        if "message can't be deleted" not in str(e) and "message to delete not found" not in str(e):
            logger.error(e)
    except Exception as e:
        logger.error(e)
    return False


def _notice_due(message: telegram_types.Message, kind: str) -> bool:
    key = (message.chat.id, message.from_user.id, kind)
    now = time.monotonic()
    if now - _last_notice.get(key, -_NOTICE_INTERVAL_SECONDS) < _NOTICE_INTERVAL_SECONDS:
        return False
    _last_notice[key] = now
    if len(_last_notice) > 10000:
        for old_key in [k for k, at in _last_notice.items() if now - at >= _NOTICE_INTERVAL_SECONDS]:
            del _last_notice[old_key]
    return True


async def _ephemeral(message: telegram_types.Message, text: str):
    try:
        await bot.send_message(
            message.chat.id, text,
            ephemeral_message_parameters=EphemeralMessageParameters(receiver_user_id=message.from_user.id))
    except (telegram_exceptions.TelegramBadRequest, telegram_exceptions.TelegramForbiddenError) as e:
        logger.warning('Cannot send an ephemeral notice', e)
    except Exception as e:
        logger.error('Cannot send an ephemeral notice', e)


async def notify_removed(message: telegram_types.Message, chat_id: int):
    """Tell the member why the message disappeared, in a message only they can see (Bot API ephemeral messages).
    On the free tariff the notice also points to the bot."""
    if not _notice_due(message, 'removed'):
        return

    language_code = message.from_user.language_code
    chat = await Chat.find(chat_id)
    if chat is not None and access.effective_mode(chat, await Chat.owner_tariff_id(chat_id)) != 'off':
        await _ephemeral(message, localization.get_message(['access', 'notice'], language_code,
                                                           link=access.join_link(chat_id)))
        return
    text = localization.get_message(['work', 'removed_notice', 'text'], language_code)
    if await Chat.owner_tariff_id(chat_id) == Tariff.FREE_TARIFF_ID:
        text += "\n\n" + localization.get_message(['work', 'removed_notice', 'promo'], language_code)
    await _ephemeral(message, text)


async def notify_over_limit(message: telegram_types.Message, limit: tuple[int, int], next_at: datetime.datetime):
    if not _notice_due(message, 'limit'):
        return

    language_code = message.from_user.language_code
    text = localization.get_message(
        ['work', 'limit_notice'], language_code, limit=post_limit.limit_text(*limit, language_code),
        wait=wait_text(next_at - datetime.datetime.now(datetime.timezone.utc), language_code))
    await _ephemeral(message, text)


def wait_text(left: datetime.timedelta, language_code: str | None) -> str:
    """"45 min", "3 h 20 min", "2 d 4 h": no clock time, which would be in a time zone not the member's."""
    minutes = max(1, -(-int(left.total_seconds()) // 60))
    days, hours, minutes = minutes // 1440, minutes % 1440 // 60, minutes % 60

    def unit(name: str, n: int) -> str:
        return localization.get_message(['work', 'wait_units', name], language_code, n=n)

    if days:
        parts = [unit('days', days)] + ([unit('hours', hours)] if hours else [])
    elif hours:
        parts = [unit('hours', hours)] + ([unit('minutes', minutes)] if minutes else [])
    else:
        parts = [unit('minutes', minutes)]
    return ' '.join(parts)
