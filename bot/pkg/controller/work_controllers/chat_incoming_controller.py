from aiogram import types, utils

from pkg.service.allowed_user import AllowedUser
from pkg.service.chat import Chat
from pkg.service.tariff import Tariff


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

    # Validate chat
    chat_data = Chat.find_by({'service_id': str(message.chat.id)})
    if chat_data is None or chat_data['disabled']:
        return

    # Validate allowed to write
    allowed: bool = AllowedUser.check_privilege(nickname, str(chat_service_id))
    if allowed:
        return

    try:
        await message.delete()
    except utils.exceptions.MessageToDeleteNotFound:
        pass
    except utils.exceptions.MessageCantBeDeleted:
        pass
