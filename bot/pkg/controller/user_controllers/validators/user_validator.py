from framework.system import telegram_types

from framework.controller.message_tools import notify
from lib.language import localization
from pkg.service.user import User


async def email_presence_validator(call: telegram_types.CallbackQuery, message: telegram_types.Message) -> bool:
    user = User.find_by_service_id(message.chat.id)
    if user['email'] is None or len(user['email']) == 0:
        await notify(None, message, localization.get_message(
            ['user', 'errors', 'email_is_none'], message.from_user.language_code))
        return False

    return True

