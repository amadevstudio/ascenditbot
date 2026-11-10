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


def _plural(count: int, one: str, few: str, many: str) -> str:
    if count % 10 == 1 and count % 100 != 11:
        return f"{count} {one}"
    if 2 <= count % 10 <= 4 and not 12 <= count % 100 <= 14:
        return f"{count} {few}"
    return f"{count} {many}"


def _groups(count: int) -> str:
    return _plural(count, "группа", "группы", "групп")


def _parts(row: dict, labels: tuple) -> str:
    """The non-zero numbers of `row` as "label N", joined by commas."""
    return ", ".join(f"{label} {row[key]}" for key, label in labels if row[key])


def format_tariffs(tariffs: list[dict], bonus: dict) -> list[str]:
    """Who is on each tariff now: on the free one all who do not pay, on a paid one split by how they got it
    (a paid tariff nobody is on is left out); and the bonus for subscribing to the channels."""
    lines = ["🎫 <b>Тарифы</b> <i>(💳 оплатили, 🧪 триал, 📢 бонус за каналы)</i>"]
    for tariff in tariffs:
        if tariff['id'] == Tariff.FREE_TARIFF_ID:
            lines.append(f"Бесплатный: {tariff['total']}")
        elif tariff['total']:
            parts = _parts(tariff, (('paid', "💳"), ('trial', "🧪"), ('bonus', "📢")))
            lines.append(f"Тариф {tariff['id']} ({_groups(tariff['channels_count'] or 0)}): {tariff['total']}"
                         + (f" – {parts}" if parts else ""))
    if bonus['taken']:
        lines.append(f"📢 Бонус за каналы взяли {bonus['taken']}"
                     + (f", отписались {bonus['lost']}" if bonus['lost'] else ""))
    return lines


def format_stats(stats: dict) -> str:
    users, groups, money = stats['users'], stats['groups'], stats['money']
    languages = _parts(users, (('ru', "ru"), ('en', "en"), ('other', "другие")))
    lines = [
        f"👥 <b>Пользователи: {users['total']}</b>" + (f" ({languages})" if languages else ""),
        f"С группами {users['with_groups']}, новые: сутки +{users['day']}, неделя +{users['week']}, "
        f"месяц +{users['month']}",
        "",
        *format_tariffs(stats['tariffs'], stats['bonus']),
        "",
        f"💬 <b>Группы: {groups['total']}</b> (модерируются {groups['on']}"
        + "".join(f", {label} {groups[key]}" for key, label in
                  (('paused', "на паузе"), ('disabled', "отключены тарифом")) if groups[key]) + ")",
        f"Пишут все {groups['everyone']}, лимит постов {groups['limited']}, "
        f"белый список {groups['whitelisted']}" + (f" (на срок {groups['timed']})" if groups['timed'] else ""),
        f"🗑 Удалено: сутки {groups['removed_day']}, неделя {groups['removed_week']}",
        "",
    ]
    payments = ", ".join(
        f"{_plural(row['count'], 'платёж', 'платежа', 'платежей')} на "
        f"{Tariff.format_amount(row['amount'], row['minor_units'])} {row['currency_code']}"
        for row in money['month']) or "платежей нет"
    balances = ", ".join(
        f"{Tariff.format_amount(row['balance'], row['minor_units'])} {row['currency_code']}"
        for row in money['balances'])
    lines.append(f"💰 <b>За 30 дней</b>: {payments}" + (f"; на балансах {balances}" if balances else ""))
    return "\n".join(lines)


async def page(params: ControllerParams):
    await message_sender(params['message'].chat.id, message_structures=[{
        'type': 'text', 'text': format_stats(await stats_repository.collect()), 'parse_mode': 'HTML',
        'reply_markup': go_back_inline_markup(params['language_code'])}])
