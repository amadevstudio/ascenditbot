from aiogram import types

from pkg.service.allowed_user import AllowedUser


async def incoming_chat_message(message: types.Message):
    # Ignore messages sent by bots
    if message.from_user.is_bot:  # and message.from_user.username != 'GroupAnonymousBot'
        return

    # Ignore messages sent by Anonymous admin
    # TODO: add to chat settings
    if message.from_user.username == 'GroupAnonymousBot':
        return

    nickname: str = message.from_user.username
    chat_service_id: int = message.chat.id

    allowed: bool = AllowedUser.check_privilege(nickname, str(chat_service_id))

    if not allowed:
        await message.delete()
