import time

from aiogram.types import EphemeralMessageParameters

from framework.system import telegram_types, telegram_exceptions
from framework.system.bot_setup import bot
from lib.language import localization
from pkg.service.allowed_user import AllowedUser
from pkg.service.chat import Chat
from pkg.service.tariff import Tariff
from pkg.system.logger import logger

# One notice per member per chat at most this often, so a flood of messages does not become a flood of notices
_NOTICE_INTERVAL_SECONDS = 600
_last_notice: dict[tuple[int, int], float] = {}


async def incoming_chat_message(message: telegram_types.Message):
    if message.from_user is None:
        logger.warning("Incoming chat message has no sender")
        return

    # Ignore messages sent by bots
    if message.from_user.is_bot:  # and message.from_user.username != 'GroupAnonymousBot'
        return

    # Ignore messages sent by Anonymous admin
    # TODO: add to chat settings
    if message.from_user.username == 'GroupAnonymousBot':
        return

    nickname: str = message.from_user.username
    chat_service_id: int = message.chat.id

    # Validate chat: unknown, over the tariff limit, or paused by the owner
    chat_data = await Chat.find_by({'service_id': str(message.chat.id)})
    if chat_data is None or chat_data['disabled'] or not chat_data['active']:
        return

    # Validate allowed to write
    allowed: bool = await AllowedUser.can_write_to_chat(nickname, str(chat_service_id))
    if allowed:
        return

    try:
        await message.delete()
    except telegram_exceptions.TelegramForbiddenError as e:
        logger.warning(e)
        return
    except telegram_exceptions.TelegramBadRequest as e:
        if "message can't be deleted" in str(e):
            return

        if "message to delete not found" in str(e):
            return

        logger.error(e)
        return
    except Exception as e:
        logger.error(e)
        return

    await Chat.restrict_user(
        chat_service_id,
        message.from_user.id,
        chat_data.get('restriction_duration_minutes', 5),
        message.chat.type)

    await notify_removed(message, chat_data['id'])


async def notify_removed(message: telegram_types.Message, chat_id: int):
    """Tell the member why the message disappeared, in a message only they can see (Bot API ephemeral messages).
    On the free tariff the notice also points to the bot."""
    key = (message.chat.id, message.from_user.id)
    now = time.monotonic()
    if now - _last_notice.get(key, -_NOTICE_INTERVAL_SECONDS) < _NOTICE_INTERVAL_SECONDS:
        return
    _last_notice[key] = now
    if len(_last_notice) > 10000:
        for old_key in [k for k, at in _last_notice.items() if now - at >= _NOTICE_INTERVAL_SECONDS]:
            del _last_notice[old_key]

    language_code = message.from_user.language_code
    text = localization.get_message(['work', 'removed_notice', 'text'], language_code)
    if await Chat.owner_tariff_id(chat_id) == Tariff.FREE_TARIFF_ID:
        text += "\n\n" + localization.get_message(['work', 'removed_notice', 'promo'], language_code)

    try:
        await bot.send_message(
            message.chat.id, text,
            ephemeral_message_parameters=EphemeralMessageParameters(receiver_user_id=message.from_user.id))
    except (telegram_exceptions.TelegramBadRequest, telegram_exceptions.TelegramForbiddenError) as e:
        logger.warning('Cannot send the removed-message notice', e)
    except Exception as e:
        logger.error('Cannot send the removed-message notice', e)
