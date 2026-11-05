"""Commands for the bot's admins (users.is_admin) in private: /usersCount (also /stats), the numbers of the bot."""
from aiogram import F, Router
from aiogram.filters import BaseFilter, Command
from aiogram.types import Message

from pkg.repository import stats_repository
from pkg.service.tariff import Tariff
from pkg.service.user import User


class BotAdmin(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        if message.from_user is None:
            return False
        user = await User.find_by_service_id(message.from_user.id)
        return user is not None and user['is_admin']


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


def admin_router() -> Router:
    router = Router()
    router.message.filter(F.chat.type == 'private')

    @router.message(Command('usersCount', 'userscount', 'stats', ignore_case=True), BotAdmin())
    async def users_count(message: Message):
        await message.answer(format_stats(await stats_repository.collect()), parse_mode='HTML')

    return router
