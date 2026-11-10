"""A bench for the bot without Telegram.

What runs is the real thing: the dispatcher with the routers `init_routes` registers (filters, middlewares, order),
the controllers, the services, the repositories, a real Postgres migrated from scratch and a real Redis. Only the
Bot API is fake: `FakeTelegram` replaces the bot's HTTP session, records every request and answers the way the
Bot API would. Nothing leaves the process.

    bench = await Bench.start()
    await bench.reset()
    owner = await bench.owner(OWNER)                      # a registered user, as after /start
    chat = await bench.group(GROUP, owner)                # a moderated group of theirs
    await bench.group_message(GROUP, STRANGER, 'hello')   # what the bot does with it
    bench.telegram.calls_of('deleteMessage')
"""
import datetime
import itertools
import os
from typing import Any

from aiogram import Bot
from aiogram.client.session.base import BaseSession
from aiogram.exceptions import TelegramBadRequest
from aiogram.methods import TelegramMethod
from aiogram.methods.base import Response
from aiogram.types import ChatMemberAdministrator, Update

BOT_ID = 100000001
BOT_USER = {'id': BOT_ID, 'is_bot': True, 'first_name': 'Ascendit', 'username': 'ascenditbot'}

# Every right an admin can have in this aiogram's Bot API, so new rights do not break the bench
_RIGHTS = tuple(
    name for name in ChatMemberAdministrator.model_fields if name.startswith('can_') and name != 'can_be_edited')


def person(user_id: int, username: str | None = None, language_code: str = 'en', first_name: str = 'Test') -> dict:
    user = {'id': user_id, 'is_bot': False, 'first_name': first_name, 'language_code': language_code}
    if username is not None:
        user['username'] = username
    return user


def administrator(user: dict, **rights: bool) -> dict:
    member = {'status': 'administrator', 'user': user, 'can_be_edited': False, 'is_anonymous': False}
    member.update({right: True for right in _RIGHTS})
    member.update(rights)
    return member


def creator(user: dict) -> dict:
    return {'status': 'creator', 'user': user, 'is_anonymous': False}


def member(user: dict) -> dict:
    return {'status': 'member', 'user': user}


class FakeTelegram(BaseSession):
    """The Bot API, answered in process. Each request is kept in `calls`; `answers` overrides a method's answer
    with a value or a function of the request, `members` and `chats` are what getChatMember and getChat see."""

    def __init__(self):
        super().__init__()
        self.calls: list[TelegramMethod] = []
        self.answers: dict[str, Any] = {}
        self.members: dict[tuple[int, int], dict] = {}
        self.chats: dict[int, dict] = {}
        self._message_ids = itertools.count(1000)

    def reset(self):
        self.calls.clear()
        self.answers.clear()
        self.members.clear()
        self.chats.clear()

    # What tests look at

    def calls_of(self, *api_methods: str) -> list[TelegramMethod]:
        return [call for call in self.calls if call.__api_method__ in api_methods]

    def sent_to(self, chat_id: int) -> list[TelegramMethod]:
        """Everything the bot posted to a chat: messages and photos, in order."""
        return [call for call in self.calls_of('sendMessage', 'sendPhoto') if call.chat_id == chat_id]

    def texts_to(self, chat_id: int) -> list[str]:
        return [getattr(call, 'text', None) or getattr(call, 'caption', None) or '' for call in self.sent_to(chat_id)]

    # The Bot API

    async def make_request(self, bot: Bot, method: TelegramMethod, timeout: int | None = None):
        self.calls.append(method)
        name = method.__api_method__

        if name in self.answers:
            answer = self.answers[name]
            result = answer(method) if callable(answer) else answer
        else:
            result = self._answer(bot, method)
        if isinstance(result, Exception):
            raise result

        response = Response[method.__returning__].model_validate(
            {'ok': True, 'result': result}, context={'bot': bot})
        return response.result

    async def stream_content(self, *args, **kwargs):
        raise NotImplementedError('the bench does not download files')
        yield b''  # pragma: no cover

    async def close(self):
        pass

    def _answer(self, bot: Bot, method: TelegramMethod):
        name = method.__api_method__

        if name == 'getMe':
            return BOT_USER

        if name in ('sendMessage', 'sendPhoto', 'editMessageText', 'editMessageCaption', 'editMessageReplyMarkup'):
            return self._message(method)

        if name == 'getChatMember':
            key = (int(method.chat_id), method.user_id)
            if key not in self.members:
                return TelegramBadRequest(method, 'Bad Request: user not found')
            return self.members[key]

        if name == 'getChatAdministrators':
            return [m for (chat_id, _), m in self.members.items()
                    if chat_id == int(method.chat_id) and m['status'] in ('administrator', 'creator')]

        if name == 'getChat':
            chat_id = int(method.chat_id)
            if chat_id not in self.chats:
                return TelegramBadRequest(method, 'Bad Request: chat not found')
            return {'accent_color_id': 0, 'max_reaction_count': 11, 'accepted_gift_types': {
                'unlimited_gifts': False, 'limited_gifts': False, 'unique_gifts': False,
                'premium_subscription': False, 'gifts_from_channels': False}, **self.chats[chat_id]}

        if method.__returning__ is bool:
            return True

        raise NotImplementedError(f'the bench has no answer for {name}: set telegram.answers[{name!r}]')

    def _message(self, method: TelegramMethod) -> dict:
        chat_id = int(method.chat_id) if getattr(method, 'chat_id', None) is not None else 0
        message = {
            'message_id': getattr(method, 'message_id', None) or next(self._message_ids),
            'date': int(datetime.datetime.now().timestamp()),
            'chat': {'id': chat_id, 'type': 'private' if chat_id > 0 else 'supergroup'},
            'from': BOT_USER,
        }
        text = getattr(method, 'text', None)
        if text is not None:
            message['text'] = text
        caption = getattr(method, 'caption', None)
        if caption is not None:
            message['caption'] = caption
        return message


class Bench:
    """The bot booted once per process, against the test database and Redis, with a fake Telegram."""

    def __init__(self):
        from framework.system.bot_setup import bot, dispatcher

        self.bot: Bot = bot
        self.dispatcher = dispatcher
        self.telegram = FakeTelegram()
        self.bot.session = self.telegram
        self._update_ids = itertools.count(1)
        self._message_ids = itertools.count(1)
        # Undone before the next case: what a case swapped in for a fake (topic_lookup.backend)
        self.cleanups: list = []

    @classmethod
    async def start(cls) -> 'Bench':
        from framework.repository.storage_connection import Storage
        from pkg.controller.router import init_routes
        from pkg.repository.database_connection import Database

        Storage().connect({
            'host': os.environ.get('TEST_REDIS_HOST', 'storage'), 'port': 6379,
            'password': os.environ['REDIS_PASSWORD']})
        await Database().connect({
            'host': os.environ.get('TEST_POSTGRES_HOST', 'db'), 'database': os.environ['POSTGRES_DB'],
            'user': os.environ['POSTGRES_USER'], 'password': os.environ['POSTGRES_PASSWORD']})

        # The paged lists (groups, the whitelist), set up as main.py does
        from lib.language import localization
        from lib.telegram.aiogram.navigation_builder import NavigationBuilder
        NavigationBuilder(localization.get_message, ["navigation_builder"])

        bench = cls()
        init_routes(bench.dispatcher)
        return bench

    async def reset(self):
        """Back to the migrated database (tariffs, prices, currencies) with no users, chats or payments."""
        from framework.repository.storage_connection import Storage
        from pkg.controller.work_controllers import chat_incoming_controller

        await self.sql("""
            TRUNCATE users, moderated_chats, allowed_users, user_moderated_chat_connections, user_tariff_connections,
                user_balances, payments_history, moderated_chat_statistics, access_requests, promo_channels,
                channel_bonus_claims
            RESTART IDENTITY CASCADE
        """)
        Storage().connection.flushdb()
        chat_incoming_controller._last_notice.clear()
        while self.cleanups:
            self.cleanups.pop()()
        self.telegram.reset()

    async def sql(self, query: str, *args) -> list[dict]:
        from pkg.repository.database_connection import Database

        async with Database().get_connection() as connection:
            return [dict(row) for row in await connection.fetch(query, *args)]

    # Setting the scene: the same services the bot uses

    async def owner(self, user: dict) -> dict:
        """A user as right after /start: registered, on the free tariff, no trial yet."""
        from pkg.service.user import User

        result = await User.register(user['id'], user.get('language_code', 'en'), {'referral': None})
        return result['user']

    def group_in_telegram(self, chat_id: int, owner: dict, chat_type: str = 'supergroup'):
        """A group as Telegram sees it: the bot an admin that deletes and restricts, the owner its creator."""
        owner_user = person(int(owner['service_id']), language_code=owner['language_code'])
        self.telegram.chats[chat_id] = {'id': chat_id, 'type': chat_type, 'title': f'Group {chat_id}'}
        self.telegram.members[(chat_id, BOT_ID)] = administrator(BOT_USER)
        self.telegram.members[(chat_id, owner_user['id'])] = creator(owner_user)

    async def group(self, chat_id: int, owner: dict, chat_type: str = 'supergroup', **fields) -> dict:
        """A group the owner connected, with `fields` of moderated_chats set (active, disabled, ...)."""
        from pkg.service.chat import Chat

        self.group_in_telegram(chat_id, owner, chat_type)
        connection = await Chat.add(chat_id, int(owner['service_id']))
        assert 'error' not in connection, f'cannot add the group: {connection}'
        if fields:
            assignments = ', '.join(f'{name} = ${i + 2}' for i, name in enumerate(fields))
            await self.sql(f'UPDATE moderated_chats SET {assignments} WHERE id = $1',
                           connection['moderated_chat_id'], *fields.values())
        self.telegram.calls.clear()
        return (await self.sql('SELECT * FROM moderated_chats WHERE id = $1', connection['moderated_chat_id']))[0]

    async def whitelist(self, chat: dict, *nicknames: str):
        from pkg.service.allowed_user import AllowedUser

        for nickname in nicknames:
            await AllowedUser.allow(chat['id'], nickname=nickname)

    # Updates in: what the dispatcher does with them

    async def feed(self, update: dict):
        update = Update.model_validate({'update_id': next(self._update_ids), **update}, context={'bot': self.bot})
        return await self.dispatcher.feed_update(self.bot, update)

    def _message(self, chat: dict, user: dict, text: str | None, **extra) -> dict:
        message = {'message_id': next(self._message_ids), 'date': int(datetime.datetime.now().timestamp()),
                   'chat': chat, 'from': user, **extra}
        if text is not None:
            message['text'] = text
            if text.startswith('/'):
                message['entities'] = [
                    {'type': 'bot_command', 'offset': 0, 'length': len(text.split()[0])}]
        return message

    async def group_message(self, chat_id: int, user: dict, text: str | None = 'hello', chat_type: str = 'supergroup',
                            forum: bool = False, **extra) -> dict:
        chat = {'id': chat_id, 'type': chat_type, 'title': f'Group {chat_id}', **({'is_forum': True} if forum else {})}
        message = self._message(chat, user, text, **extra)
        await self.feed({'message': message})
        return message

    async def private_message(self, user: dict, text: str | None, **extra) -> dict:
        chat = {'id': user['id'], 'type': 'private', 'first_name': user.get('first_name', 'Test')}
        message = self._message(chat, user, text, **extra)
        await self.feed({'message': message})
        return message

    async def tap(self, user: dict, data: str, message_id: int = 1) -> None:
        chat = {'id': user['id'], 'type': 'private', 'first_name': user.get('first_name', 'Test')}
        await self.feed({'callback_query': {
            'id': str(next(self._update_ids)), 'from': user, 'chat_instance': '1', 'data': data,
            'message': {'message_id': message_id, 'date': int(datetime.datetime.now().timestamp()),
                        'chat': chat, 'from': BOT_USER, 'text': '...'}}})
