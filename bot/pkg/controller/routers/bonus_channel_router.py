"""Joins and leaves in the bonus channels (pkg/service/channel_bonus.py): chat_member, sent to the channel's admins,
checks the bonus at once. The channels are listed in the admin pages (pkg/controller/admin_controllers)."""
from aiogram import F, Router
from aiogram.types import ChatMemberUpdated

from pkg.service.channel_bonus import ChannelBonus
from pkg.system.logger import logger


def bonus_channel_router() -> Router:
    router = Router()

    @router.chat_member(F.chat.type == 'channel')
    async def channel_membership(event: ChatMemberUpdated):
        """Left or joined a bonus channel: no waiting for the daily check."""
        from pkg.background.async_tasks.subscription_handler import notify_bonus_lost
        was, now = ChannelBonus.in_channel(event.old_chat_member), ChannelBonus.in_channel(event.new_chat_member)
        if was == now:
            return
        try:
            await ChannelBonus.membership_changed(
                str(event.chat.id), event.new_chat_member.user.id, now, notify_bonus_lost)
        except Exception as e:
            logger.error(e, 'Channel bonus: cannot handle a membership change', event.chat.id)

    return router
