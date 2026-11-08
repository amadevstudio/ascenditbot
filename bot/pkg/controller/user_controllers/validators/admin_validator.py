from framework.system import telegram_types

from pkg.service.user import User


async def admin_validator(call: telegram_types.CallbackQuery, message: telegram_types.Message) -> bool:
    """The admin pages are for the bot's owners (users.is_admin): a button from anyone else does nothing."""
    user = await User.find_by_service_id(message.chat.id)
    return user is not None and bool(user['is_admin'])
