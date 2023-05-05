from framework.controller.message_tools import chat_id_sender
from pkg.config.config import environment
from framework.system.bot_setup import bot


class MessageSender:
    @staticmethod
    async def notify_admins(text: str):
        telegram_admin_group_id = environment.get('TELEGRAM_ADMIN_GROUP_ID', None)
        if telegram_admin_group_id is not None:
            await chat_id_sender(int(telegram_admin_group_id), message_structures=[{
                'type': 'text',
                'text': text
            }])
