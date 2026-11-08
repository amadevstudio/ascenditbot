"""/stats in private shows the user their groups. The hidden /usersCount command opens the same admin-only
bot statistics page as Menu → Admin → Bot, through its existing route and access validator."""
import asyncio
import html
from decimal import Decimal

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from lib.language import localization
from pkg.repository import access_repository, stats_repository
from pkg.service import access
from pkg.service.chat import Chat
from pkg.service.user import User
from pkg.system.logger import logger

# A message holds 4096 characters: the groups past this many are only counted
GROUPS_SHOWN = 20


async def _member_count(bot, service_id: str) -> int | None:
    try:
        return await bot.get_chat_member_count(int(service_id))
    except Exception as e:
        # Removed from the group, or the group is gone: shown without the number
        logger.warning('Cannot count the members of a group', service_id, e)
        return None


def _number(value: int | None) -> str:
    return '–' if value is None else f'{value:,}'.replace(',', ' ')


def _collapsed(lines: list[str]) -> str:
    """An expandable quote: one line shown, the rest behind a tap (quotes cannot be nested)."""
    return "<blockquote expandable>" + "\n".join(lines) + "</blockquote>"


async def format_owner_stats(bot, user_id: int | None, language_code: str) -> str:
    """The summary of the user's groups, then each group in a collapsed quote."""
    def text(key: str, **kwargs) -> str:
        return localization.get_message(['stats', key], language_code, **kwargs)

    groups = await stats_repository.owner_groups(user_id) if user_id is not None else []
    if not groups:
        return text('no_groups')

    counts = await asyncio.gather(*(_member_count(bot, group['service_id']) for group in groups))
    on = sum(1 for group in groups if group['active'] and not group['disabled'])
    summary = [
        text('title', count=len(groups), on=on, off=len(groups) - on),
        text('members', count=_number(sum(known) if (known := [c for c in counts if c is not None]) else None)),
        text('whitelist', count=sum(g['whitelisted'] for g in groups), timed=sum(g['timed'] for g in groups)),
        text('removed', day=sum(g['removed_day'] for g in groups), week=sum(g['removed_week'] for g in groups),
             month=sum(g['removed_month'] for g in groups)),
    ]
    payments = await access_repository.payments_of_owner(user_id)

    def paid_line(rows: list[dict]) -> list[str]:
        if not rows:
            return []
        totals: dict[str, Decimal] = {}
        for row in rows:
            totals[row['currency']] = totals.get(row['currency'], Decimal(0)) + Decimal(str(row['amount']))
        return [text('payments', count=sum(row['count'] for row in rows), amount=' + '.join(
            access.format_amount(amount, currency) for currency, amount in sorted(totals.items())))]

    summary += paid_line(payments)
    details = []
    for group, count in list(zip(groups, counts))[:GROUPS_SHOWN]:
        state = 'disabled' if group['disabled'] else 'paused' if not group['active'] else 'on'
        details += [
            *([""] if details else []),
            f"<b>{html.escape(await Chat.name_of(group) or str(group['service_id']))}</b>",
            localization.get_message(['chat', 'show', 'state', state], language_code),
            text('group_members', count=_number(count)) + " · " + text(
                'group_whitelist', count=group['whitelisted'], timed=group['timed']),
            text('removed', day=group['removed_day'], week=group['removed_week'], month=group['removed_month']),
            *paid_line([row for row in payments if row['chat_id'] == group['id']]),
        ]
    if len(groups) > GROUPS_SHOWN:
        details += ["", text('more', count=len(groups) - GROUPS_SHOWN)]
    return "\n".join(summary) + "\n" + _collapsed(details)


def stats_router() -> Router:
    router = Router()
    router.message.filter(F.chat.type == 'private')

    @router.message(Command('stats', ignore_case=True))
    async def stats(message: Message):
        user = await User.find_by_service_id(message.from_user.id) if message.from_user else None
        language_code = (user or {}).get('language_code') or (
            message.from_user.language_code if message.from_user else None) or 'en'
        text = await format_owner_stats(message.bot, user['id'] if user else None, language_code)
        await message.answer(text, parse_mode='HTML', disable_web_page_preview=True)

    return router
