"""The user blocks or unblocks the bot: Telegram sends my_chat_member in the private chat. Kept in users.blocked_at
for the admin numbers (pkg/repository/stats_repository.py): the people the bot can still reach."""
from aiogram import F, Router
from aiogram.types import ChatMemberUpdated

from pkg.repository import user_repository
from pkg.system.logger import logger


def private_status_router() -> Router:
    router = Router()

    @router.my_chat_member(F.chat.type == 'private')
    async def private_status_changed(event: ChatMemberUpdated):
        blocked = event.new_chat_member.status == 'kicked'
        try:
            await user_repository.set_blocked(str(event.chat.id), blocked)
        except Exception as e:
            logger.error(e, 'Private status: cannot save', event.chat.id, blocked)

    return router
