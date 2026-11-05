"""The command menus of the bot (setMyCommands), set on every start so that the code is the one place they live:
in private for everyone, in groups for their admins (/allow, /deny, /settings), and in the private chats of the
bot's admins with /usersCount on top."""
from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScope, BotCommandScopeAllChatAdministrators, \
    BotCommandScopeAllPrivateChats, BotCommandScopeChat, BotCommandScopeDefault

from lib.language import localization
from pkg.repository import user_repository
from pkg.system.logger import logger

PRIVATE = ['menu', 'my_chats', 'add_chat', 'subscription', 'settings', 'help']
GROUP = ['allow', 'deny', 'settings']
# Telegram takes only lowercase commands in a menu; /usersCount works in any case
ADMIN = ['userscount']

# The menu in English for every language but Russian
LANGUAGES = [None, 'ru']


def commands(kind: str, names: list[str], language_code: str | None) -> list[BotCommand]:
    return [BotCommand(command=name, description=localization.get_message(
        ['commands', kind, name], language_code or 'en')) for name in names]


def admin_commands(language_code: str | None) -> list[BotCommand]:
    return commands('private', PRIVATE, language_code) + commands('admin', ADMIN, language_code)


async def _set(bot: Bot, scope: BotCommandScope, build) -> None:
    for language_code in LANGUAGES:
        await bot.set_my_commands(build(language_code), scope=scope, language_code=language_code)


async def set_bot_commands(bot: Bot) -> None:
    try:
        await _set(bot, BotCommandScopeAllPrivateChats(), lambda lang: commands('private', PRIVATE, lang))
        # No menu by default (it was set in BotFather once), so members of groups see none: the group commands
        # are for admins and are ignored from others
        for language_code in LANGUAGES:
            await bot.delete_my_commands(scope=BotCommandScopeDefault(), language_code=language_code)
        await _set(bot, BotCommandScopeAllChatAdministrators(), lambda lang: commands('group', GROUP, lang))
        for service_id in await user_repository.admin_service_ids():
            await _set(bot, BotCommandScopeChat(chat_id=int(service_id)), admin_commands)
    except Exception as e:
        # A menu is a convenience: the bot works without it
        logger.error('Cannot set the command menus', e)
