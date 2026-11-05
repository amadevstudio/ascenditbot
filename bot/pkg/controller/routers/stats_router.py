"""/usersCount (also /stats) in private, in two modes: a group owner sees their groups (members, whitelist, removed
messages), the bot's owner (users.is_admin) sees the whole bot and then their own groups."""
import asyncio
import html

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from lib.language import localization
from pkg.repository import stats_repository
from pkg.service.chat import Chat
from pkg.service.tariff import Tariff
from pkg.service.user import User
from pkg.system.logger import logger

# A message holds 4096 characters: the groups past this many are only counted
GROUPS_SHOWN = 20


def format_stats(stats: dict) -> str:
    users, groups, money = stats['users'], stats['groups'], stats['money']
    lines = [
        "<b>Пользователи</b>",
        f"Всего: {users['total']} (ru {users['ru']}, en {users['en']}, другие {users['other']})",
        f"Новых: сутки {users['day']}, неделя {users['week']}, месяц {users['month']}",
        f"С группами: {users['with_groups']}",
        f"Тариф: бесплатный {users['free']}, платный {users['paid']} (из них на триале {users['trial']})",
        "",
        "<b>Группы</b>",
        f"Всего: {groups['total']}",
        f"Модерируются: {groups['on']}, на паузе: {groups['paused']}, отключены тарифом: {groups['disabled']}",
        f"Пишут все (с лимитом): {groups['everyone']}, с лимитом постов: {groups['limited']}",
        f"В белых списках: {groups['whitelisted']} (на срок: {groups['timed']})",
        f"Удалено сообщений: сутки {groups['removed_day']}, неделя {groups['removed_week']}",
        "",
        "<b>Деньги</b>",
    ]
    if money['month']:
        lines.append("Платежи за 30 дней: " + ", ".join(
            f"{row['count']} на {Tariff.format_amount(row['amount'], row['minor_units'])} {row['currency_code']}"
            for row in money['month']))
    else:
        lines.append("Платежей за 30 дней нет")
    if money['balances']:
        lines.append("На балансах: " + ", ".join(
            f"{Tariff.format_amount(row['balance'], row['minor_units'])} {row['currency_code']}"
            for row in money['balances']))
    return "\n".join(lines)


async def _member_count(bot, service_id: str) -> int | None:
    try:
        return await bot.get_chat_member_count(int(service_id))
    except Exception as e:
        # Removed from the group, or the group is gone: shown without the number
        logger.warning('Cannot count the members of a group', service_id, e)
        return None


def _number(value: int | None) -> str:
    return '–' if value is None else f'{value:,}'.replace(',', ' ')


async def format_owner_stats(bot, user_id: int | None, language_code: str) -> str:
    def text(key: str, **kwargs) -> str:
        return localization.get_message(['stats', key], language_code, **kwargs)

    groups = await stats_repository.owner_groups(user_id) if user_id is not None else []
    if not groups:
        return text('no_groups')

    counts = await asyncio.gather(*(_member_count(bot, group['service_id']) for group in groups))
    on = sum(1 for group in groups if group['active'] and not group['disabled'])
    lines = [
        text('title', count=len(groups), on=on, off=len(groups) - on),
        text('members', count=_number(sum(known) if (known := [c for c in counts if c is not None]) else None)),
        text('whitelist', count=sum(g['whitelisted'] for g in groups), timed=sum(g['timed'] for g in groups)),
        text('removed', day=sum(g['removed_day'] for g in groups), week=sum(g['removed_week'] for g in groups),
             month=sum(g['removed_month'] for g in groups)),
    ]
    for group, count in list(zip(groups, counts))[:GROUPS_SHOWN]:
        state = 'disabled' if group['disabled'] else 'paused' if not group['active'] else 'on'
        lines += [
            "",
            f"<b>{html.escape(await Chat.name_of(group) or str(group['service_id']))}</b>",
            localization.get_message(['chat', 'show', 'state', state], language_code),
            text('group_members', count=_number(count)) + " · " + text(
                'group_whitelist', count=group['whitelisted'], timed=group['timed']),
            text('removed', day=group['removed_day'], week=group['removed_week'], month=group['removed_month']),
        ]
    if len(groups) > GROUPS_SHOWN:
        lines += ["", text('more', count=len(groups) - GROUPS_SHOWN)]
    return "\n".join(lines)


def stats_router() -> Router:
    router = Router()
    router.message.filter(F.chat.type == 'private')

    @router.message(Command('usersCount', 'userscount', 'stats', ignore_case=True))
    async def users_count(message: Message):
        user = await User.find_by_service_id(message.from_user.id) if message.from_user else None
        language_code = (user or {}).get('language_code') or (
            message.from_user.language_code if message.from_user else None) or 'en'
        owner_text = await format_owner_stats(message.bot, user['id'] if user else None, language_code)
        if user is not None and user['is_admin']:
            # The extended mode: the whole bot first, then the owner's own groups
            text = format_stats(await stats_repository.collect()) + "\n\n" + owner_text
        else:
            text = owner_text
        await message.answer(text, parse_mode='HTML', disable_web_page_preview=True)

    return router
