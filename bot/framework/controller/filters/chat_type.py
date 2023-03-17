from typing import Union

from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery

from lib.telegram.aiogram.message_processor import call_and_message_accessed_processor


class ChatTypeFilter(BaseFilter):
    def __init__(self, chat_type: Union[str, list]):
        self.chat_type = chat_type

    async def __call__(self, entity: Message | CallbackQuery) -> bool:
        call, message = call_and_message_accessed_processor(entity)

        if isinstance(self.chat_type, str):
            return message.chat.type == self.chat_type
        else:
            return message.chat.type in self.chat_type
