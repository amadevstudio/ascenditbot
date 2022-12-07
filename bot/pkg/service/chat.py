import datetime

import aiogram.bot.bot
from aiogram import types
from aiogram.utils import exceptions

from pkg.repository import chat_repository
from pkg.system.logger import logger

chat_interface = {
    'id': int,
    'service_id': str,
    'active': bool,
    'disabled': bool,
    'allow_administrators': bool,
    'allowed_keywords': str,
    'created_at': datetime.datetime,
    'updated_at': datetime.datetime
}


class Chat:
    @staticmethod
    def find(chat_id: int):
        return chat_repository.find(chat_id)

    @staticmethod
    async def _validate_bot_rights(bot: aiogram.bot.bot.Bot, chat_service_id: int):
        try:
            chat_member = await bot.get_chat_member(chat_service_id, bot.id)
        except exceptions.Unauthorized:
            return {'error': 'not_member'}
        except exceptions.ChatNotFound:
            return {'error': 'not_found'}
        except Exception as e:
            logger.err(e)
            return {'error': 'unknown'}

        if chat_member.status == "user":
            return {'error': 'not_admin'}

        # Unresolved attribute reference 'can_delete_messages' for class 'ChatMember'
        # It works, but using hash interface don't warn
        # if chat_member.can_delete_messages is False:
        if chat_member['can_delete_messages'] is False:
            return {'error': 'cant_edit_messages'}

        return {}

    @staticmethod
    async def _validate_admin_rights(bot: aiogram.bot.bot.Bot, chat_service_id: int, user_service_id: int):
        chat_administrators = await bot.get_chat_administrators(chat_service_id)
        administrator: types.ChatMemberAdministrator | types.ChatMemberOwner | None = None

        for chat_administrator in chat_administrators:
            if chat_administrator.user.id == user_service_id:
                administrator = chat_administrator

        if administrator is None:
            return {"error": "user_not_admin"}

        if administrator.can_delete_messages is False:
            return {"error": "user_cant_edit_messages"}

        return {"administrator": administrator}

    @staticmethod
    async def add(bot: aiogram.bot.bot.Bot, chat_service_id: int, user_service_id: int):
        # Validate we are admin with deletion rights
        result = await Chat._validate_bot_rights(bot, chat_service_id)
        if "error" in result:
            return {"error": result["error"]}

        # Validate client is an admin with edit rights too
        result = await Chat._validate_admin_rights(bot, chat_service_id, user_service_id)
        if "error" in result:
            return {"error": result["error"]}

        # administrator = result["administrator"]
        # TODO: validate administrator.status == 'creator' without premium subscription

        try:
            result_connection = chat_repository.create(str(chat_service_id), str(user_service_id))
            if "error" in result_connection:
                return result_connection
        except Exception as e:
            logger.err(e)
            return {"error": "unexpected"}

        return result_connection

    @staticmethod
    async def get_info(bot: aiogram.bot.bot.Bot, chat_service_id: str):
        chat_info = await bot.get_chat(chat_service_id)
        return {
            'service_id': chat_info['id'],
            'title': chat_info['title']
        }

    @staticmethod
    def data_count_provider(user_id: int):
        return chat_repository.user_chats_count(str(user_id))

    @staticmethod
    def data_count_provider_by_service_id(chat_id: int):
        return chat_repository.user_chats_count_by_service_id(str(chat_id))

    @staticmethod
    def data_provider(user_id: int, order_by: str, limit: int, offset: int):
        return chat_repository.user_chats(str(user_id), order_by, limit, offset)

    @staticmethod
    def data_provider_by_service_id(chat_id: int, order_by: str, limit: int, offset: int):
        return chat_repository.user_chats_by_service_id(str(chat_id), order_by, limit, offset)

    @staticmethod
    def switch_active(chat_id: int):
        return chat_repository.switch_active(chat_id)
