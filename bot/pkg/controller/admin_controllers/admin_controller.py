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


def format_tariffs(tariffs: list[dict], bonus: dict) -> list[str]:
    """Who is on each tariff now, the tariff named by its price in rubles and its groups: on the free one all who do
    not pay, on a paid one split by how they got it (a paid tariff nobody is on is left out); and the bonus for
    subscribing to the channels."""
    lines = ["🎫 <b>Тарифы</b> <i>(💳 оплатили, 🧪 триал, 📢 бонус за каналы)</i>"]
    for tariff in tariffs:
        groups = _groups(tariff['channels_count'] or 0)
        if tariff['id'] == Tariff.FREE_TARIFF_ID:
            lines.append(f"Бесплатный · {groups}: {tariff['total']}")
        elif tariff['total']:
            name = _money(tariff['price'], 2, 'rub') if tariff['price'] is not None else f"Тариф {tariff['id']}"
            parts = _parts(tariff, (('paid', "💳"), ('trial', "🧪"), ('bonus', "📢")))
            lines.append(f"{name} · {groups}: {tariff['total']}" + (f" ({parts})" if parts else ""))
    if bonus['taken']:
        lines.append(f"📢 Бонус за каналы взяли {bonus['taken']}"
                     + (f", отписались {bonus['lost']}" if bonus['lost'] else ""))
    return lines


def format_stats(stats: dict) -> str:
    """The bot's numbers, a section a header with its main number; zeros left out."""
    users, groups, money = stats['users'], stats['groups'], stats['money']
    languages = _parts(users, (('ru', "ru"), ('en', "en"), ('other', "другие")))
    states = _parts(groups, (('on', "работают"), ('paused', "на паузе"), ('disabled', "отключены тарифом")))
    modes = _parts(groups, (('everyone', "пишут все"), ('limited', "с лимитом постов")))
    lines = [
        f"👥 <b>Пользователи: {users['total']}</b>" + (f" ({languages})" if languages else ""),
        f"С группами {users['with_groups']} · новые: +{users['day']} за сутки, +{users['week']} за неделю, "
        f"+{users['month']} за месяц",
        "",
        *format_tariffs(stats['tariffs'], stats['bonus']),
        "",
        f"💬 <b>Группы: {groups['total']}</b>" + (f" ({states})" if states else ""),
    ]
    if modes:
        lines.append(f"⚙️ {modes[0].upper()}{modes[1:]}")
    if groups['whitelisted']:
        lines.append(f"✅ В белых списках {groups['whitelisted']}"
                     + (f", из них на срок {groups['timed']}" if groups['timed'] else ""))
    lines.append(f"🗑 Удалено сообщений: {groups['removed_day']} за сутки, {groups['removed_week']} за неделю")
    payments = ", ".join(
        f"{_plural(row['count'], 'платёж', 'платежа', 'платежей')} на "
        f"{_money(row['amount'], row['minor_units'], row['currency_code'])}"
        for row in money['month']) or "платежей нет"
    balances = ", ".join(_money(row['balance'], row['minor_units'], row['currency_code'])
                         for row in money['balances'])
    lines += ["", f"💰 <b>За 30 дней</b>: {payments}" + (f" · на балансах {balances}" if balances else "")]
    return "\n".join(lines)


async def page(params: ControllerParams):
    await message_sender(params['message'].chat.id, message_structures=[{
        'type': 'text', 'text': format_stats(await stats_repository.collect()), 'parse_mode': 'HTML',
        'reply_markup': go_back_inline_markup(params['language_code'])}])
