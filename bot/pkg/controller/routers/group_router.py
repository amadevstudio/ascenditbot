"""What admins do in the group itself, and what happens when the bot is made an admin there.

- /allow and /deny, in reply to a member's message or with @nicknames, ids or t.me links (and a term: 7d),
  put members on the whitelist or take them off without opening the bot.
- /settings opens the group's page in the private chat with the bot (connecting the group first if needed).
- Made an admin of a group by its owner, the bot connects it on its own and sends the owner its page.

The commands are deleted from the group; the answers are ephemeral (only the admin sees them)."""
import datetime
import html

import aiogram
from aiogram import F, Router
from aiogram.filters import BaseFilter, Command, CommandObject
from aiogram.types import ChatMemberUpdated, EphemeralMessageParameters, Message

from framework.system import telegram_exceptions, telegram_types
from framework.system.bot_setup import bot
from lib.language import localization
from pkg.controller.routers.quick_actions_router import lift_restriction
from pkg.service.allowed_user import AllowedUser, full_name, parse_member_words, parse_term
from pkg.service.chat import Chat
from pkg.service.member_alerts import format_date
from pkg.service.tariff import Tariff
from pkg.service.user import User
from pkg.system.logger import logger
from project import constants

GROUP_TYPES = (aiogram.enums.chat_type.ChatType.GROUP, aiogram.enums.chat_type.ChatType.SUPERGROUP)
_TELEGRAM_SERVICE_ID = 777000


class GroupAdmin(BaseFilter):
    """The sender administers the group: its owner, an admin, or an anonymous admin (the group itself)."""

    async def __call__(self, message: Message) -> bool | dict:
        if message.sender_chat is not None and message.sender_chat.id == message.chat.id:
            return {'admin': None}
        if message.from_user is None or message.from_user.is_bot:
            return False
        if await Chat.is_administrator(message.chat.id, message.from_user.id):
            return {'admin': message.from_user}
        return False


def deep_link(chat_id: int) -> str:
    return f"https://t.me/{constants.bot_nickname}?start=chat_{chat_id}"


async def _answer(message: Message, admin, text: str):
    """Only the admin sees the answer; an anonymous admin, who cannot be addressed, gets an ordinary reply."""
    try:
        if admin is not None:
            await bot.send_message(message.chat.id, text, parse_mode='HTML', disable_web_page_preview=True,
                                   ephemeral_message_parameters=EphemeralMessageParameters(receiver_user_id=admin.id))
        else:
            await bot.send_message(message.chat.id, text, parse_mode='HTML', disable_web_page_preview=True)
    except (telegram_exceptions.TelegramBadRequest, telegram_exceptions.TelegramForbiddenError) as e:
        logger.warning('Cannot answer a group command', e)


async def _delete(message: Message):
    try:
        await message.delete()
    except (telegram_exceptions.TelegramBadRequest, telegram_exceptions.TelegramForbiddenError):
        pass


def _private_message(user: telegram_types.User) -> Message:
    """A stand-in for a message in the private chat with `user`, to open a page there from the group."""
    return Message(message_id=0, date=datetime.datetime.now(datetime.timezone.utc),
                   chat=telegram_types.Chat(id=user.id, type='private', first_name=user.first_name),
                   from_user=user).as_(bot)


async def _open_page(user: telegram_types.User, chat_id: int) -> bool:
    """The group's page in the user's private chat with the bot; False when the bot cannot write to them."""
    # Imported here: the user controllers import the routes, which import them back
    from pkg.controller.user_controllers.chats_controller import open_chat_page

    if await User.find_by_service_id(user.id) is None:
        return False
    try:
        return await open_chat_page(_private_message(user), chat_id, user.language_code)
    except Exception as e:
        logger.warning('Cannot open the group page in private', e)
        return False


async def _connect(chat_service_id: int, user: telegram_types.User) -> dict:
    """Connects the group for this user; {'error': ...} when they cannot (not its owner, not registered)."""
    if await User.find_by_service_id(user.id) is None:
        return {'error': 'not_registered'}
    result = await Chat.add(chat_service_id, user.id)
    if 'error' in result and result['error'] != 'connection_exists':
        return result
    connection = result.get('connection', result)
    await Chat.update_names(user.id)
    return {'moderated_chat_id': connection['moderated_chat_id']}


def _targets(message: Message, words: list[str]) -> tuple[list[dict], list[str]]:
    members, unknown = parse_member_words(' '.join(words))
    replied = message.reply_to_message
    if replied is not None and replied.from_user is not None and not replied.from_user.is_bot \
            and replied.from_user.id != _TELEGRAM_SERVICE_ID:
        sender = replied.from_user
        members.insert(0, {'user_service_id': str(sender.id), 'nickname': sender.username,
                           'display_name': full_name(sender)})
    return members, unknown


def _member_text(member: dict) -> str:
    if member.get('nickname'):
        return '@' + html.escape(member['nickname'])
    return html.escape(member.get('display_name') or f"id {member.get('user_service_id')}")


def group_router() -> Router:
    router = Router()
    router.message.filter(F.chat.type.in_(GROUP_TYPES))

    @router.message(Command('allow', 'deny'), GroupAdmin())
    async def allow_or_deny(message: Message, command: CommandObject, admin):
        language_code = admin.language_code if admin is not None else None
        await _delete(message)

        chat = await Chat.find_by({'service_id': str(message.chat.id)})
        if chat is None:
            await _answer(message, admin, localization.get_message(['group', 'not_connected'], language_code))
            return

        days, words = parse_term((command.args or '').split())
        members, unknown = _targets(message, words)
        if not members:
            await _answer(message, admin, localization.get_message(
                ['group', 'usage', command.command], language_code))
            return

        if command.command == 'deny':
            for member in members:
                await AllowedUser.disallow(chat['id'], member.get('user_service_id'), member.get('nickname'))
            text = localization.get_message(['group', 'denied'], language_code,
                                            members=', '.join(map(_member_text, members)))
        else:
            if days and not Tariff.is_paid(await Chat.owner_tariff_id(chat['id'])):
                await _answer(message, admin, localization.get_message(['alerts', 'paid_only'], language_code))
                return
            for member in members:
                await AllowedUser.allow(chat['id'], **member, days=days)
                if member.get('user_service_id'):
                    await lift_restriction(message.chat.id, int(member['user_service_id']))
            names = ', '.join(map(_member_text, members))
            if days:
                text = localization.get_message(
                    ['group', 'allowed_until'], language_code, members=names,
                    date=format_date(datetime.datetime.now() + datetime.timedelta(days=days)))
            else:
                text = localization.get_message(['group', 'allowed'], language_code, members=names)
        if unknown:
            text += "\n" + localization.get_message(
                ['group', 'not_understood'], language_code, words=html.escape(', '.join(unknown)))
        await _answer(message, admin, text)

    @router.message(Command('settings', 'ascendit'), GroupAdmin())
    async def settings(message: Message, admin):
        language_code = admin.language_code if admin is not None else None
        await _delete(message)

        chat = await Chat.find_by({'service_id': str(message.chat.id)})
        if admin is None:
            # An anonymous admin cannot be written to in private: a link they open themselves
            if chat is not None:
                await _answer(message, admin, localization.get_message(
                    ['group', 'settings_link'], language_code, link=deep_link(chat['id'])))
            return

        if chat is None:
            connected = await _connect(message.chat.id, admin)
            if 'error' in connected:
                key = 'register_first' if connected['error'] == 'not_registered' else 'cannot_connect'
                await _answer(message, admin, localization.get_message(
                    ['group', key], language_code, bot=constants.bot_nickname,
                    reason=localization.get_message(['access', 'chat', 'errors', connected['error']], language_code)))
                return
            chat_id = connected['moderated_chat_id']
        else:
            chat_id = chat['id']

        if await _open_page(admin, chat_id):
            await _answer(message, admin, localization.get_message(
                ['group', 'settings_sent'], language_code, bot=constants.bot_nickname))
        else:
            await _answer(message, admin, localization.get_message(
                ['group', 'settings_link'], language_code, link=deep_link(chat_id)))

    @router.my_chat_member(F.chat.type.in_(GROUP_TYPES))
    async def bot_status_changed(event: ChatMemberUpdated):
        """Made an admin that can delete messages: connect the group for the one who did it and send them its
        page. Added without those rights: tell them what is missing."""
        user = event.from_user
        if user is None or user.is_bot:
            return
        new = event.new_chat_member
        language_code = user.language_code
        if await User.find_by_service_id(user.id) is None:
            return  # never started the bot: it cannot write to them

        if new.status == 'administrator' and getattr(new, 'can_delete_messages', False):
            connected = await _connect(event.chat.id, user)
            if 'error' in connected:
                await _dm(user, localization.get_message(
                    ['group', 'auto_connect_failed'], language_code, chat_name=html.escape(event.chat.title or ''),
                    reason=localization.get_message(['access', 'chat', 'errors', connected['error']], language_code)))
                return
            await _dm(user, localization.get_message(
                ['group', 'auto_connected'], language_code, chat_name=html.escape(event.chat.title or '')))
            await _open_page(user, connected['moderated_chat_id'])
        elif new.status in ('member', 'administrator'):
            await _dm(user, localization.get_message(
                ['group', 'needs_admin'], language_code, chat_name=html.escape(event.chat.title or '')))

    return router


async def _dm(user: telegram_types.User, text: str):
    try:
        await bot.send_message(user.id, text, parse_mode='HTML', disable_web_page_preview=True)
    except (telegram_exceptions.TelegramBadRequest, telegram_exceptions.TelegramForbiddenError) as e:
        logger.warning('Cannot write to the user', user.id, e)
