from aiogram import types

from pkg.controller.work_controllers.chat_incoming_controller import incoming_chat_message


def work_router(dispatcher):
    @dispatcher.message_handler(
        chat_type=types.ChatType.GROUP, content_types=types.ContentType.ANY)
    @dispatcher.message_handler(
        chat_type=types.ChatType.SUPERGROUP, content_types=types.ContentType.ANY)
    async def main_message_filter(message: types.Message):
        await incoming_chat_message(message)
