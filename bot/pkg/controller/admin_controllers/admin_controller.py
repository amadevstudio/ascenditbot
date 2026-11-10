"""The admin pages for the bot's owners (users.is_admin), from "🛠 Админка" in the menu: the menu of them and the numbers
of the whole bot (users, groups, removed messages, money). The pages are in Russian: they are the owner's."""
from framework.controller.message_tools import go_back_inline_markup, message_sender
from framework.controller.types import ControllerParams
from pkg.repository import stats_repository
from pkg.service.tariff import Tariff


async def menu(params: ControllerParams):
    await message_sender(params['message'].chat.id, message_structures=[{
        'type': 'text', 'text': "<b>Админка</b>", 'parse_mode': 'HTML',
        'reply_markup': [
            [{'text': "📊 Бот", 'callback_data': {'tp': 'admin_bot'}}],
            [{'text': "🔗 Источники", 'callback_data': {'tp': 'admin_sources'}}],
            [{'text': "📢 Каналы за подписку", 'callback_data': {'tp': 'admin_channels'}}],
            *go_back_inline_markup(params['language_code'])]}])


def _groups(count: int) -> str:
    if count % 10 == 1 and count % 100 != 11:
        return f"{count} группа"
    if 2 <= count % 10 <= 4 and not 12 <= count % 100 <= 14:
        return f"{count} группы"
    return f"{count} групп"


def format_tariffs(tariffs: list[dict], bonus: dict) -> list[str]:
    """Who is on each tariff now: on the free one all who do not pay, on a paid one split by how they got it."""
    lines = ["<b>Тарифы</b>"]
    for tariff in tariffs:
        name = "Бесплатный" if tariff['id'] == Tariff.FREE_TARIFF_ID else f"Тариф {tariff['id']}"
        line = f"{name} ({_groups(tariff['channels_count'] or 0)}): {tariff['total']}"
        if tariff['id'] != Tariff.FREE_TARIFF_ID and tariff['total']:
            parts = [f"{label} {tariff[key]}" for key, label in
                     (('paid', "оплатили"), ('trial', "триал"), ('bonus', "бонус за каналы")) if tariff[key]]
            line += " – " + ", ".join(parts)
        lines.append(line)
    lines.append(f"Бонус за подписку на каналы взяли: {bonus['taken']}"
                 + (f", сейчас отписаны: {bonus['lost']}" if bonus['lost'] else ""))
    return lines


def format_stats(stats: dict) -> str:
    users, groups, money = stats['users'], stats['groups'], stats['money']
    lines = [
        "<b>Пользователи</b>",
        f"Всего: {users['total']} (ru {users['ru']}, en {users['en']}, другие {users['other']})",
        f"Новых: сутки {users['day']}, неделя {users['week']}, месяц {users['month']}",
        f"С группами: {users['with_groups']}",
        "",
        *format_tariffs(stats['tariffs'], stats['bonus']),
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


async def page(params: ControllerParams):
    await message_sender(params['message'].chat.id, message_structures=[{
        'type': 'text', 'text': format_stats(await stats_repository.collect()), 'parse_mode': 'HTML',
        'reply_markup': go_back_inline_markup(params['language_code'])}])
