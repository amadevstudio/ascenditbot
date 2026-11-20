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


_SYMBOLS = {'rub': "₽", 'usd': "$", 'xtr': "⭐"}


def _money(amount: int, minor_units: int, currency_code: str) -> str:
    """2 250 ₽, 12,50 $, 350 ⭐; a currency without a symbol by its code."""
    value = Tariff.format_amount(amount, minor_units)
    number = f"{value:,.2f}" if value != int(value) else f"{int(value):,}"
    return f"{number.replace(',', ' ').replace('.', ',')} {_SYMBOLS.get(currency_code, currency_code.upper())}"


# Telegram keeps no-break spaces at a line's start: the lines of a section stand under its header
INDENT = "\u00a0" * 4


def _groups_limit(channels_count: int | None) -> str:
    """A tariff's groups: none stored is no limit."""
    return "без лимита" if channels_count is None else _groups(channels_count)


def _section(header: str, rows: list[str]) -> list[str]:
    return [header, *(INDENT + row for row in rows if row)]


def format_tariffs(tariffs: list[dict], bonus: dict) -> list[str]:
    """Who is on each tariff now (the bot's admins left out), the tariff named by its price in rubles and its groups:
    on the free one all who do not pay, on a paid one split by how they got it (a paid tariff nobody is on is left
    out); the bonus for subscribing to the channels; the legend last, when a paid tariff is there."""
    rows, paid_shown = [], False
    for tariff in tariffs:
        groups = _groups_limit(tariff['channels_count'])
        if tariff['id'] == Tariff.FREE_TARIFF_ID:
            rows.append(f"Бесплатный, {groups}: {tariff['total']}")
        elif tariff['total']:
            name = _money(tariff['price'], 2, 'rub') if tariff['price'] is not None else f"Тариф {tariff['id']}"
            parts = _parts(tariff, (('paid', "💳"), ('paid_before', "↩️"), ('trial', "🧪"), ('bonus', "📢")))
            rows.append(f"{name}, {groups}: {tariff['total']}" + (f" ({parts})" if parts else ""))
            paid_shown = True
    if bonus['taken']:
        rows.append(f"Бонус за каналы: взяли {bonus['taken']}"
                    + (f", отписались {bonus['lost']}" if bonus['lost'] else ""))
    lines = _section("🎫 <b>Тарифы</b>", rows)
    if paid_shown:
        lines.append("<i>💳 платят сейчас · ↩️ платили раньше · 🧪 триал · 📢 бонус</i>")
    return lines


def format_stats(stats: dict) -> str:
    """The bot's numbers: a section a header and its lines indented under it, a blank line between sections; zeros
    left out where they say nothing."""
    users, groups, money = stats['users'], stats['groups'], stats['money']
    languages = _parts(users, (('ru', "ru"), ('en', "en"), ('other', "другие"))).replace(", ", " · ")
    states = _parts(groups, (('on', "работают"), ('paused', "на паузе"), ('disabled', "отключены тарифом")))
    blocked = (f"Заблокировали бота: {users['blocked']}, могут получать сообщения {users['total'] - users['blocked']}"
               if users['blocked'] else "")
    whitelist = (f"В белых списках: {groups['whitelisted']}"
                 + (f", из них на срок {groups['timed']}" if groups['timed'] else "")) if groups['whitelisted'] else ""
    payments = ", ".join(
        f"{_plural(row['count'], 'платёж', 'платежа', 'платежей')} на "
        f"{_money(row['amount'], row['minor_units'], row['currency_code'])}"
        for row in money['month']) or "Платежей нет"
    balances = ", ".join(_money(row['balance'], row['minor_units'], row['currency_code'])
                         for row in money['balances'])
    lines = [
        *_section(f"👥 <b>Пользователи: {users['total']}</b>", [
            languages,
            blocked,
            f"С группами: {users['with_groups']}",
            f"Новые: +{users['day']} за сутки, +{users['week']} за неделю, +{users['month']} за месяц",
        ]),
        "",
        *format_tariffs(stats['tariffs'], stats['bonus']),
        "",
        *_section(f"💬 <b>Группы: {groups['total']}</b>", [
            states.replace(", ", " · ").capitalize(),
            f"Пишут все: {groups['everyone']}" if groups['everyone'] else "",
            f"С лимитом постов: {groups['limited']}" if groups['limited'] else "",
            whitelist,
            f"Продают доступ: {_groups(groups['selling'])}, продаж за 30 дней: {groups['sales_month']}",
            f"Удалено сообщений: {groups['removed_day']} за сутки, {groups['removed_week']} за неделю",
        ]),
        "",
        *_section("💰 <b>Деньги за 30 дней</b>", [
            payments[0].upper() + payments[1:],
            f"На балансах: {balances}" if balances else "",
        ]),
    ]
    return "\n".join(lines)


async def page(params: ControllerParams):
    await message_sender(params['message'].chat.id, message_structures=[{
        'type': 'text', 'text': format_stats(await stats_repository.collect()), 'parse_mode': 'HTML',
        'reply_markup': go_back_inline_markup(params['language_code'])}])
