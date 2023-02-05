from aiogram import types

from framework.controller.message_tools import notify
from lib.language import localization
from pkg.service.user import User


async def email_presence_validator(call: types.CallbackQuery, message: types.Message) -> bool:
    user = User.find_by_service_id(message.chat.id)
    if user['email'] is None:
        await notify(None, message, localization.get_message(
            ['user', 'errors', 'email_is_none'], message.from_user.language_code))
        return False

    return True

