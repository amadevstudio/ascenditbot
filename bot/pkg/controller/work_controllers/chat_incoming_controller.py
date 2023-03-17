from framework.system import telegram_types, telegram_exceptions
from pkg.service.allowed_user import AllowedUser
from pkg.service.tariff import Tariff
from pkg.system.logger import logger


async def incoming_chat_message(message: telegram_types.Message):
    # Ignore messages sent by bots
    if message.from_user.is_bot:  # and message.from_user.username != 'GroupAnonymousBot'
        return

    # Ignore messages sent by Anonymous admin
    # TODO: add to chat settings
    if message.from_user.username == 'GroupAnonymousBot':
        return

    nickname: str = message.from_user.username
    chat_service_id: int = message.chat.id

    # Validate owner subscription
    if not Tariff.validity_for_moderation(chat_service_id):
        return

    # Validate allowed to write
    allowed: bool = AllowedUser.check_privilege(nickname, str(chat_service_id))
    if allowed:
        return

    try:
        await message.delete()
    except telegram_exceptions.TelegramBadRequest as e:
        if "message can't be deleted" in str(e):
            return

        if "message to delete not found" in str(e):
            return

        logger.err(e)
