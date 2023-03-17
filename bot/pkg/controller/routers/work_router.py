import aiogram
from aiogram import Router

from framework.controller.filters.chat_type import ChatTypeFilter
from framework.system import telegram_types

from pkg.controller.work_controllers.chat_incoming_controller import incoming_chat_message

GROUP = aiogram.enums.chat_type.ChatType.GROUP
SUPERGROUP = aiogram.enums.chat_type.ChatType.SUPERGROUP


def work_router():
    router = Router()

    @router.message(ChatTypeFilter([GROUP, SUPERGROUP]))
    async def main_message_filter(message: telegram_types.Message):
        await incoming_chat_message(message)

    return router
