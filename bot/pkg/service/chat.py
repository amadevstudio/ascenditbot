import asyncio
import datetime
import typing
from typing import TypedDict, List, Literal

from framework.system import telegram_types, telegram_exceptions

import pkg.repository.chat_repository
from framework.system.bot_setup import bot
from pkg.repository import chat_repository
from pkg.service.service import Service
from pkg.service.tariff import Tariff
from pkg.service.user import User
from pkg.system.logger import logger
from project.types import ModeratedChatInterface, ErrorDictInterface, AllowedUserInterface


class AdminValidationInterface(TypedDict, total=False):
    administrator: telegram_types.ChatMemberAdministrator | telegram_types.ChatMemberOwner


class AccessValidationInterface(ErrorDictInterface, total=False):
    administrator: telegram_types.ChatMemberAdministrator | telegram_types.ChatMemberOwner
    chat_info: ModeratedChatInterface


class Chat(Service):
    BOT = bot

    @staticmethod
    def _chat_type_value(chat_type) -> str:
        return getattr(chat_type, 'value', chat_type)

    @staticmethod
    async def find(chat_id: int) -> ModeratedChatInterface | None:
        return await chat_repository.find(chat_id)

    @staticmethod
    async def owner_tariff_id(chat_id: int) -> int | None:
        return await chat_repository.owner_tariff_id(chat_id)

    @staticmethod
    async def find_by(chat: ModeratedChatInterface) -> ModeratedChatInterface | None:
        return await chat_repository.find_by(chat)

    @staticmethod
    async def update_settings(chat_id: int, settings: dict) -> ModeratedChatInterface | None:
        return await chat_repository.update_settings(chat_id, settings)

    @staticmethod
    async def removed_count(chat_id: int, days: int) -> int:
        return await chat_repository.removed_count(chat_id, days)

    @staticmethod
    async def neighbours(chat_id: int, user_service_id: int) -> tuple[int | None, int | None]:
        return await chat_repository.neighbours(chat_id, str(user_service_id))

    @staticmethod
    async def is_manager(chat_id: int, user_service_id: int) -> bool:
        return await chat_repository.is_manager(chat_id, str(user_service_id))

    @classmethod
    async def _get_chat_member(cls, chat_service_id: int, user_id: int) \
            -> telegram_types.ChatMember | ErrorDictInterface:
        try:
            chat_member = await cls.BOT.get_chat_member(chat_service_id, user_id)
            return chat_member
        except telegram_exceptions.TelegramForbiddenError:
            return {'error': 'not_member'}
        except telegram_exceptions.TelegramBadRequest:
            return {'error': 'not_found'}
        except Exception as e:
            logger.error(e)
            return {'error': 'unknown'}

    @classmethod
    async def is_administrator(cls, chat_service_id: int, user_service_id: int) -> bool:
        """The member is the group's owner or one of its admins (False when Telegram cannot say)."""
        chat_member = await cls._get_chat_member(chat_service_id, user_service_id)
        if isinstance(chat_member, dict):
            return False
        return chat_member.status in ('creator', 'administrator')

    @classmethod
    async def bot_rights_problem(cls, chat_service_id: int | str) -> Literal['no_rights', 'not_in_group'] | None:
        """What keeps the bot from moderating the group: 'not_in_group' (removed, or the group is gone),
        'no_rights' (a plain member, or an admin that cannot delete); None when it can, or Telegram did not say.
        Rights are checked when a group is connected, but an owner may take them away later."""
        try:
            chat_member = await cls._get_chat_member(int(chat_service_id), bot.id)
        except Exception as e:
            logger.warning('Cannot check the bot rights', chat_service_id, e)
            return None
        if isinstance(chat_member, dict) or chat_member.status in ('left', 'kicked'):
            return 'not_in_group'
        if chat_member.status != 'administrator' or not getattr(chat_member, 'can_delete_messages', False):
            return 'no_rights'
        return None

    @classmethod
    async def working_groups_without_rights(cls, user_id: int) -> list[ModeratedChatInterface]:
        """The user's switched-on groups where the bot cannot delete messages."""
        chats = await chat_repository.user_working_chats(user_id)
        problems = await asyncio.gather(*(cls.bot_rights_problem(chat['service_id']) for chat in chats))
        return [chat for chat, problem in zip(chats, problems) if problem is not None]

    @staticmethod
    async def _validate_bot_rights(chat_member: telegram_types.ChatMember) -> ErrorDictInterface:
        if chat_member.status in ['user', 'member'] or chat_member.can_delete_messages is None:
            return {'error': 'not_admin'}

        # Unresolved attribute reference 'can_delete_messages' for class 'ChatMember'
        # It works, but using hash interface don't warn
        # if chat_member.can_delete_messages is False:
        if chat_member.can_delete_messages is False:
            return {'error': 'cant_edit_messages'}

        return {}

    @classmethod
    async def _validate_admin_rights(cls, chat_service_id: int, user_service_id: int) \
            -> ErrorDictInterface | AdminValidationInterface:
        chat_administrators = await cls.BOT.get_chat_administrators(chat_service_id)
        administrator: telegram_types.ChatMemberAdministrator | telegram_types.ChatMemberOwner | None = None

        for chat_administrator in chat_administrators:
            if chat_administrator.user.id == user_service_id:
                administrator = chat_administrator
                break

        if administrator is None:
            return {'error': 'user_not_admin'}

        if isinstance(administrator, telegram_types.ChatMemberOwner):
            return {'administrator': administrator}

        if isinstance(administrator, telegram_types.ChatMemberAdministrator):
            if administrator.can_delete_messages:
                return {'administrator': administrator}
            return {'error': 'user_cant_edit_messages'}

        return {'error': 'user_not_admin'}

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
            telegram_types.ChatMemberAdministrator | telegram_types.ChatMemberOwner,
            admin_rights_validation['administrator'])

        chat_info = await chat_repository.find_by({'service_id': str(chat_service_id)})
        exists_in_the_bot = chat_info is not None

        if not exists_in_the_bot:
            if administrator.status != 'creator':
                return {'error': 'creator_must_add'}

        return {'administrator': administrator, 'chat_info': chat_info}

    @staticmethod
    async def validate_subscription(
            administrator: telegram_types.ChatMemberAdministrator | telegram_types.ChatMemberOwner,
            user_service_id: int,
            chat_info: ModeratedChatInterface) -> ErrorDictInterface:

        exists_in_the_bot = chat_info is not None

        if exists_in_the_bot:
            creator = None

            if administrator.status == 'creator':
                creator = await User.find_by_service_id(user_service_id)

            if administrator.status != 'creator' or creator is None:
                creator = await chat_repository.chat_creator(chat_info['id'])

            # Due to a possible random error, the chat may not have a creator
            if creator is None:
                return {'error': 'creator_must_add'}

        # Not exists in the bot
        else:
            creator = await User.find_by_service_id(user_service_id)
            if creator is None:
                return {'error': 'creator_must_add'}

        # Creator is another, check if the chat is active, chat exists
        if str(user_service_id) != creator['service_id']:
            if chat_info['disabled']:
                return {'error': 'creator_dont_subscribed'}

        # Creator is the user, check subscription limitation, chat not exists or not due a possible random error
        else:
            already_added = chat_info is not None
            if not already_added and not (await Tariff.chats_number_satisfactory(int(creator['service_id']))):
                return {'error': 'subscription_limit_violation'}

        return {}

    @classmethod
    async def add(cls, chat_service_id: int, user_service_id: int) \
            -> ModeratedChatInterface | ErrorDictInterface:

        validate_access_result = await cls.validate_access(chat_service_id, user_service_id)
        if 'error' in validate_access_result:
            return validate_access_result

        validate_subscription_result = await cls.validate_subscription(
            validate_access_result['administrator'], user_service_id, validate_access_result['chat_info'])
        if 'error' in validate_subscription_result:
            return validate_subscription_result

        is_creator = validate_access_result['administrator'].status == 'creator'

        try:
            result_connection = await chat_repository.create(
                str(chat_service_id), str(user_service_id), is_creator)
            if "error" in result_connection:
                return result_connection
        except Exception as e:
            logger.error(e)
            return {"error": "unexpected"}

        return result_connection

    @classmethod
    async def load_info(cls, chat_service_id: str) \
            -> TypedDict('_', {'service_id': str, 'title': str, 'nickname': str | None}) | ErrorDictInterface:
        try:
            chat_info: telegram_types.Chat = await cls.BOT.get_chat(chat_service_id)
        except telegram_exceptions.TelegramBadRequest:
            return {'error': "chat_not_found"}

        chat_title = chat_info.title if chat_info.title is not None else ''
        chat_nickname = chat_info.username

        return {
            'service_id': str(chat_info.id),
            'title': chat_title,
            'nickname': chat_nickname
        }

    @staticmethod
    async def data_count_provider(user_id: int) -> int | None:
        return await chat_repository.user_chats_count(str(user_id))

    @staticmethod
    async def data_count_provider_by_service_id(user_chat_id: int, search_query: str | None = None) -> int | None:
        return await chat_repository.user_chats_count_by_service_id(str(user_chat_id), search_query)

    @staticmethod
    async def data_provider(user_id: int, order_by: str, limit: int, offset: int) -> List[ModeratedChatInterface]:
        return await chat_repository.user_chats(str(user_id), order_by, limit, offset)

    @staticmethod
    async def data_provider_by_service_id(
            user_chat_id: int, search_query: str | None = None,
            order_by: Literal['name', 'created_at'] = 'name', limit: int | None = None, offset: int = 0)\
            -> List[ModeratedChatInterface]:
        return await chat_repository.user_chats_by_service_id(str(user_chat_id), search_query, order_by, limit, offset)

    @staticmethod
    async def switch_active(chat_id: int) -> bool:
        return await chat_repository.switch_active(chat_id)

    @staticmethod
    async def update_restriction_duration(chat_id: int, duration_minutes: int) -> int:
        return await chat_repository.update_restriction_duration(chat_id, duration_minutes)

    @classmethod
    async def validate_restriction_access(cls, chat_service_id: int) -> ErrorDictInterface:
        try:
            chat_info = await cls.BOT.get_chat(chat_service_id)
        except telegram_exceptions.TelegramForbiddenError:
            return {'error': 'not_member'}
        except telegram_exceptions.TelegramBadRequest:
            return {'error': 'not_found'}
        except Exception as e:
            logger.error(e)
            return {'error': 'unknown'}

        if cls._chat_type_value(chat_info.type) != 'supergroup':
            return {'error': 'restriction_supergroup_required'}

        chat_member = await cls._get_chat_member(chat_service_id, bot.id)
        if 'error' in chat_member:
            return {'error': chat_member['error']}

        bot_rights_validation = await cls._validate_bot_rights(chat_member)
        if 'error' in bot_rights_validation:
            return {'error': bot_rights_validation['error']}

        if isinstance(chat_member, telegram_types.ChatMemberOwner):
            return {}

        if isinstance(chat_member, telegram_types.ChatMemberAdministrator) and chat_member.can_restrict_members:
            return {}

        return {'error': 'cant_restrict_members'}

    @classmethod
    async def restrict_user(
            cls, chat_service_id: int, user_service_id: int, duration_minutes: int, chat_type: str | None = None,
            is_admin: bool | None = None):
        """Mutes the member for a while after a removed message. The owner and the admins are not muted (with
        admins not allowed to write their messages only go): Telegram refuses it, "can't remove chat owner".
        `is_admin` when the caller knows it already, so it is not asked again."""
        if duration_minutes <= 0 or cls._chat_type_value(chat_type) != 'supergroup':
            return
        if is_admin is None:
            is_admin = await cls.is_administrator(chat_service_id, user_service_id)
        if is_admin:
            return

        try:
            until_date = (
                datetime.datetime.now(datetime.timezone.utc)
                + datetime.timedelta(minutes=duration_minutes))
            await cls.BOT.restrict_chat_member(
                chat_id=chat_service_id,
                user_id=user_service_id,
                permissions=telegram_types.ChatPermissions(can_send_messages=False),
                until_date=until_date)
        except (telegram_exceptions.TelegramBadRequest, telegram_exceptions.TelegramForbiddenError) as e:
            logger.warning(e)
        except Exception as e:
            logger.error(e)

    @staticmethod
    async def delete(chat_id: int, user_service_id: int) -> int | ErrorDictInterface:
        try:
            chat_info = await chat_repository.find(chat_id)
            if chat_info is None:
                return {'error': 'not_found'}

            validate_access_result = await Chat.validate_access(int(chat_info['service_id']), user_service_id)
            if 'error' in validate_access_result:
                return validate_access_result

            if validate_access_result['administrator'].status != 'creator':
                return {'error': 'owner_must_delete'}

            delete_result = await chat_repository.delete(chat_id)
            return {'error': 'not_found'} if delete_result is None else delete_result
        except Exception as e:
            logger.error(e)
            return {'error': 'unexpected'}

    @staticmethod
    async def whitelist_summary(chat_id: int) -> dict:
        return dict(await chat_repository.whitelist_summary(chat_id) or {'writing': 0, 'off': 0, 'ended': 0})

    @staticmethod
    async def delete_ended(chat_id: int) -> int:
        return await chat_repository.delete_ended(chat_id)

    @classmethod
    async def member_names(cls, chat_service_id: int, user_service_id: int) -> tuple[str | None, str] | None:
        """The member's username and name as Telegram has them, when they are in the group."""
        chat_member = await cls._get_chat_member(chat_service_id, user_service_id)
        if isinstance(chat_member, dict) or chat_member.user is None:
            return None
        user = chat_member.user
        return user.username, ' '.join(part for part in (user.first_name, user.last_name) if part)

    @staticmethod
    async def whitelist_data_count_provider(chat_id: int, search_query: str | None = None) -> int:
        return await chat_repository.chat_whitelist_count(chat_id, search_query)

    @staticmethod
    async def whitelist_data_provider(
            chat_id: int, search_query: str | None = None,
            order_by: Literal['created_at', 'nickname'] = 'nickname', limit: int | None = None, offset: int = 0) \
            -> list[AllowedUserInterface] | None:
        return await pkg.repository.chat_repository.chat_whitelist(chat_id, search_query, order_by, limit, offset)

    @classmethod
    async def name_of(cls, chat: ModeratedChatInterface) -> str:
        """The group's title: the saved one, else asked from Telegram and saved."""
        if chat.get('name'):
            return chat['name']
        chat_info = await cls.load_info(chat_service_id=str(chat['service_id']))
        if 'error' in chat_info:
            return ''
        await chat_repository.update({'id': chat['id'], 'name': chat_info['title']})
        return chat_info['title']

    @classmethod
    async def update_names(cls, user_service_id: int):
        user_chats = await cls.data_provider_by_service_id(user_service_id)
        for chat in user_chats:
            chat_info = await cls.load_info(chat_service_id=str(chat['service_id']))
            if 'error' in chat_info:
                continue

            await chat_repository.update({'id': chat['id'], 'name': chat_info['title']})
