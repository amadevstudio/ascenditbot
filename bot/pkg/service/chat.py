from typing import TypedDict, List, Literal

import aiogram.bot.bot
from aiogram import types
from aiogram.utils import exceptions

import pkg.repository.allowed_user_repository
import pkg.repository.chat_repository
from pkg.repository import chat_repository
from pkg.system.logger import logger
from project.types import ChatInterface, ErrorDictInterface


class Chat:
    @staticmethod
    def find(chat_id: int) -> ChatInterface | None:
        return chat_repository.find(chat_id)

    @staticmethod
    async def _get_chat_member(bot: aiogram.bot.bot.Bot, chat_service_id: int, user_id: int) \
            -> types.ChatMember | ErrorDictInterface:
        try:
            chat_member = await bot.get_chat_member(chat_service_id, user_id)
            return chat_member
        except exceptions.Unauthorized:
            return {'error': 'not_member'}
        except exceptions.ChatNotFound:
            return {'error': 'not_found'}
        except Exception as e:
            logger.err(e)
            return {'error': 'unknown'}

    @staticmethod
    async def _validate_bot_rights(chat_member: types.chat_member) -> ErrorDictInterface:
        if chat_member.status == "user":
            return {'error': 'not_admin'}

        # Unresolved attribute reference 'can_delete_messages' for class 'ChatMember'
        # It works, but using hash interface don't warn
        # if chat_member.can_delete_messages is False:
        if chat_member['can_delete_messages'] is False:
            return {'error': 'cant_edit_messages'}

        return {}

    @staticmethod
    async def _validate_admin_rights(bot: aiogram.bot.bot.Bot, chat_service_id: int, user_service_id: int) \
            -> ErrorDictInterface | TypedDict('_', {'administrator': types.ChatMember}):
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
    async def validate_access(bot: aiogram.bot.bot.Bot, chat_service_id: int, user_service_id: int) \
            -> ErrorDictInterface:
        # Validate we are admin with deletion rights
        chat_member = await Chat._get_chat_member(bot, chat_service_id, bot.id)
        if "error" in chat_member:
            return {"error": chat_member["error"]}

        result = await Chat._validate_bot_rights(chat_member)
        if "error" in result:
            return {"error": result["error"]}

        # Validate client is an admin with edit rights too
        result = await Chat._validate_admin_rights(bot, chat_service_id, user_service_id)
        if "error" in result:
            return {"error": result["error"]}

        # administrator = result["administrator"]
        # TODO: validate administrator.status == 'creator' without premium subscription

        return {}

    @staticmethod
    async def add(bot: aiogram.bot.bot.Bot, chat_service_id: int, user_service_id: int) \
            -> ChatInterface | ErrorDictInterface:

        validate_result = await Chat.validate_access(bot, chat_service_id, user_service_id)
        if 'error' in validate_result:
            return validate_result

        try:
            result_connection = chat_repository.create(str(chat_service_id), str(user_service_id))
            if "error" in result_connection:
                return result_connection
        except Exception as e:
            logger.err(e)
            return {"error": "unexpected"}

        return result_connection

    @staticmethod
    async def load_info(bot: aiogram.bot.bot.Bot, chat_service_id: str) \
            -> TypedDict('_', {'service_id': str, 'title': str}):
        chat_info: types.Chat = await bot.get_chat(chat_service_id)
        return {
            'service_id': str(chat_info['id']),
            'title': chat_info['title']
        }

    @staticmethod
    def data_count_provider(user_id: int) -> int | None:
        return chat_repository.user_chats_count(str(user_id))

    @staticmethod
    def data_count_provider_by_service_id(user_chat_id: int) -> int | None:
        return chat_repository.user_chats_count_by_service_id(str(user_chat_id))

    @staticmethod
    def data_provider(user_id: int, order_by: str, limit: int, offset: int) -> List[ChatInterface]:
        return chat_repository.user_chats(str(user_id), order_by, limit, offset)

    @staticmethod
    def data_provider_by_service_id(
            chat_service_id: int, order_by: str, limit: int, offset: int) -> List[ChatInterface]:
        return chat_repository.user_chats_by_service_id(str(chat_service_id), order_by, limit, offset)

    @staticmethod
    def switch_active(chat_id: int) -> bool:
        return chat_repository.switch_active(chat_id)

    @staticmethod
    def add_to_whitelist(chat_id: int, user_nickname: str) -> ChatInterface | None | ErrorDictInterface:
        # chat_member = await Chat._get_chat_member(bot, chat_service_id, user_)
        # if "error" in chat_member:
        #     return {"error": chat_member["error"]}

        try:
            result_whitelisted = chat_repository.add_to_whitelist(chat_id, user_nickname)
        except Exception as e:
            logger.err(e)
            return {"error": "unexpected"}

        return result_whitelisted

    @staticmethod
    def whitelist_data_count_provider(chat_id: int) -> int:
        return chat_repository.chat_whitelist_count(chat_id)

    @staticmethod
    def whitelist_data_provider(chat_id: int, order_by: str, limit: int, offset: int):
        return pkg.repository.chat_repository.chat_whitelist(chat_id, order_by, limit, offset)
