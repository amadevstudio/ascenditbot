import json
import os
from datetime import datetime, timezone

from aiogram import F, Router

from framework.system import telegram_types
from pkg.system.logger import logger

# Messages users send to the Direct Messages of the bot's channel (the bot is its admin) are kept in a
# local JSON Lines file next to the bot logs, so the owner can read the feedback. bot/logs/ is not in git.
_FILE = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'logs', 'direct_messages.jsonl')


def direct_messages_router():
    router = Router()

    @router.message(F.chat.is_direct_messages)
    async def save_direct_message(message: telegram_types.Message):
        sender = message.from_user
        record = {
            'date': message.date.astimezone(timezone.utc).isoformat(),
            'saved_at': datetime.now(timezone.utc).isoformat(),
            'chat_id': message.chat.id,
            'topic_id': message.direct_messages_topic.topic_id if message.direct_messages_topic else None,
            'message_id': message.message_id,
            'from_id': sender.id if sender else None,
            'from_username': sender.username if sender else None,
            'from_name': sender.full_name if sender else None,
            'text': message.text or message.caption,
            'has_media': bool(message.photo or message.document or message.voice or message.video),
        }
        try:
            with open(_FILE, 'a', encoding='utf-8') as f:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
        except OSError as e:
            logger.error('Cannot save a direct message', e)

    return router
