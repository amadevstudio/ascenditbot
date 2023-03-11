import typing
from typing import TypedDict, List, Literal

import aiogram
from aiogram import types, exceptions

import pkg.repository.allowed_user_repository
import pkg.repository.chat_repository
from pkg.controller.bot_setup import bot
from pkg.repository import chat_repository
from pkg.service.service import Service
from pkg.service.tariff import Tariff
from pkg.service.user import User
from pkg.system.logger import logger
from project.types import ModeratedChatInterface, ErrorDictInterface, AllowedUserInterface


class AdminValidationInterface(TypedDict, total=False):
    administrator: types.ChatMemberAdministrator | types.ChatMemberOwner


class AccessValidationInterface(ErrorDictInterface, total=False):
    administrator: types.ChatMemberAdministrator | types.ChatMemberOwner
    chat_info: ModeratedChatInterface


class Chat(Service):
    BOT = bot

    @staticmethod
    def find(chat_id: int) -> ModeratedChatInterface | None:
        return chat_repository.find(chat_id)

    @classmethod
    async def _get_chat_member(cls, chat_service_id: int, user_id: int) \
            -> types.ChatMember | ErrorDictInterface:
        try:
            chat_member = await cls.BOT.get_chat_member(chat_service_id, user_id)
            return chat_member
        # except exceptions.Unauthorized:
        #     return {'error': 'not_member'}
        # except exceptions.ChatNotFound:
        #     return {'error': 'not_found'}
        except Exception as e:
            logger.err(e)
            return {'error': 'unknown'}

    @staticmethod
    async def _validate_bot_rights(chat_member: types.ChatMember) -> ErrorDictInterface:
        if chat_member.status in ['user', 'member'] or 'can_delete_messages' not in chat_member:
            return {'error': 'not_admin'}

        # Unresolved attribute reference 'can_delete_messages' for class 'ChatMember'
        # It works, but using hash interface don't warn
        # if chat_member.can_delete_messages is False:
        if chat_member['can_delete_messages'] is False:
            return {'error': 'cant_edit_messages'}

        return {}

    @classmethod
    async def _validate_admin_rights(cls, chat_service_id: int, user_service_id: int) \
            -> ErrorDictInterface | AdminValidationInterface:
        chat_administrators = await cls.BOT.get_chat_administrators(chat_service_id)
        administrator: types.ChatMemberAdministrator | types.ChatMemberOwner | None = None

        for chat_administrator in chat_administrators:
            if chat_administrator.user.id == user_service_id:
                administrator = chat_administrator

        if administrator is None:
            return {'error': 'user_not_admin'}

        if administrator.can_delete_messages is False:
            return {'error': 'user_cant_edit_messages'}

        return {'administrator': administrator}

    @classmethod
    async def validate_access(cls, chat_service_id: int, user_service_id: int) \
            -> AccessValidationInterface:
        # Validate we are admin with deletion rights
        chat_member = await cls._get_chat_member(chat_service_id, bot.id)
        if 'error' in chat_member:
            return {'error': chat_member['error']}

        bot_rights_validation = await cls._validate_bot_rights(chat_member)
        if 'error' in bot_rights_validation:
            return {'error': bot_rights_validation['error']}

        # Validate client is an admin with edit rights too
        admin_rights_validation = await cls._validate_admin_rights(chat_service_id, user_service_id)
        if 'error' in admin_rights_validation:
            return {'error': admin_rights_validation['error']}

        administrator = typing.cast(
            types.ChatMemberAdministrator | types.ChatMemberOwner, admin_rights_validation['administrator'])

        chat_info = chat_repository.find_by({'service_id': str(chat_service_id)})
        exists_in_the_bot = chat_info is not None

        if not exists_in_the_bot:
            if administrator.status != 'creator':
                return {'error': 'creator_must_add'}

        return {'administrator': administrator, 'chat_info': chat_info}

    @staticmethod
    def validate_subscription(
            administrator: types.ChatMemberAdministrator | types.ChatMemberOwner,
            user_service_id: int,
            chat_info: ModeratedChatInterface) -> ErrorDictInterface:

        exists_in_the_bot = chat_info is not None

        if exists_in_the_bot:
            creator = None

            if administrator.status == 'creator':
                creator = User.find_by_service_id(user_service_id)

            if administrator.status != 'creator' or creator is None:
                creator = chat_repository.chat_creator(chat_info['id'])

            # Due to a possible random error, the chat may not have a creator
            if creator is None:
                return {'error': 'creator_must_add'}

        # Not exists in the bot
        else:
            creator = User.find_by_service_id(user_service_id)
            if creator is None:
                return {'error': 'creator_must_add'}

        # Creator is another, check if the chat is active, chat exists
        if str(user_service_id) != creator['service_id']:
            if chat_info['disabled']:
                return {'error': 'creator_dont_subscribed'}

        # Creator is the user, check subscription limitation, chat not exists or not due a possible random error
        else:
            already_added = chat_info is not None
            if not already_added and not Tariff.chats_number_satisfactory(int(creator['service_id'])):
                return {'error': 'subscription_limit_violation'}

        return {}

    @classmethod
    async def add(cls, chat_service_id: int, user_service_id: int) \
            -> ModeratedChatInterface | ErrorDictInterface:

        validate_access_result = await cls.validate_access(chat_service_id, user_service_id)
        if 'error' in validate_access_result:
            return validate_access_result

        validate_subscription_result = cls.validate_subscription(
            validate_access_result['administrator'], user_service_id, validate_access_result['chat_info'])
        if 'error' in validate_subscription_result:
            return validate_subscription_result

        is_creator = validate_access_result['administrator'].status == 'creator'

        try:
            result_connection = chat_repository.create(
                str(chat_service_id), str(user_service_id), is_creator)
            if "error" in result_connection:
                return result_connection
        except Exception as e:
            logger.err(e)
            return {"error": "unexpected"}

        return result_connection

    @classmethod
    async def load_info(cls, chat_service_id: str) \
            -> TypedDict('_', {'service_id': str, 'title': str}) | ErrorDictInterface:
        # try:
        chat_info: types.Chat = await cls.BOT.get_chat(chat_service_id)
        # except aiogram.utils.exceptions.ChatNotFound:
        #     return {'error': "chat_not_found"}

        return {
            'service_id': str(chat_info['id']),
            'title': chat_info['title']
        }

    @staticmethod
    def data_count_provider(user_id: int) -> int | None:
        return chat_repository.user_chats_count(str(user_id))

    @staticmethod
    def data_count_provider_by_service_id(user_chat_id: int, search_query: str | None = None) -> int | None:
        return chat_repository.user_chats_count_by_service_id(str(user_chat_id), search_query)

    @staticmethod
    def data_provider(user_id: int, order_by: str, limit: int, offset: int) -> List[ModeratedChatInterface]:
        return chat_repository.user_chats(str(user_id), order_by, limit, offset)

    @staticmethod
    def data_provider_by_service_id(
            user_chat_id: int, search_query: str | None = None,
            order_by: Literal['name', 'created_at'] = 'name', limit: int | None = None, offset: int = 0)\
            -> List[ModeratedChatInterface]:
        return chat_repository.user_chats_by_service_id(str(user_chat_id), search_query, order_by, limit, offset)

    @staticmethod
    def switch_active(chat_id: int) -> bool:
        return chat_repository.switch_active(chat_id)

    @staticmethod
    def add_to_whitelist(chat_id: int, user_nickname: str) -> ModeratedChatInterface | None | ErrorDictInterface:
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
    def whitelist_data_count_provider(chat_id: int, search_query: str | None = None) -> int:
        return chat_repository.chat_whitelist_count(chat_id, search_query)

    @staticmethod
    def whitelist_data_provider(
            chat_id: int, search_query: str | None = None,
            order_by: Literal['created_at', 'nickname'] = 'nickname', limit: int | None = None, offset: int = 0) \
            -> list[AllowedUserInterface] | None:
        return pkg.repository.chat_repository.chat_whitelist(chat_id, search_query, order_by, limit, offset)

    @classmethod
    async def update_names(cls, user_service_id: int):
        user_chats = cls.data_provider_by_service_id(user_service_id)
        for chat in user_chats:
            chat_info = await cls.load_info(chat_service_id=str(chat['service_id']))
            if 'error' in chat_info:
                continue

            chat_repository.update({'id': chat['id'], 'name': chat_info['title']})
