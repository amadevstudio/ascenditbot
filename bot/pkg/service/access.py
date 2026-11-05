"""The way into a group through the bot, for people off its whitelist.

The owner picks a mode on the group's page: off, by request (free: the member asks, a manager approves) or paid
(prices and a way to pay; on a paid tariff). A member opens the group's page in the bot from the link in the
notice about a deleted message, or from a message the owner posted in the group, and asks or pays there.

Prices are written the way people write them, one per line: "7 300", "30 days 1000 ₽", "month 10$",
"forever 3000". Stored as [{"days": 30, "amount": "1000", "currency": "RUB"}], days 0 for good."""
import datetime
import json
import re
from decimal import Decimal, InvalidOperation

from lib.language import localization
from pkg.repository import access_repository, allowed_user_repository
from pkg.service.allowed_user import AllowedUser
from pkg.service.tariff import Tariff
from project import constants

MODES = ('off', 'request', 'paid')
MAX_PLANS = 5
MAX_DAYS = 3650
MAX_AMOUNT = Decimal('10000000')
TERMS_LENGTH = 1000
PAYMENT_LENGTH = 500
# A member may ask again (or remind the owner) this long after the last request
REPEAT_AFTER = datetime.timedelta(hours=12)

CURRENCIES = {
    'RUB': {'symbol': '₽', 'before': False},
    'USD': {'symbol': '$', 'before': True},
    'EUR': {'symbol': '€', 'before': False},
    'USDT': {'symbol': 'USDT', 'before': False},
    'TON': {'symbol': 'TON', 'before': False},
}
_CURRENCY_WORDS = {
    '₽': 'RUB', 'р': 'RUB', 'руб': 'RUB', 'рублей': 'RUB', 'рубля': 'RUB', 'рубль': 'RUB', 'rub': 'RUB',
    'rur': 'RUB',
    '$': 'USD', 'usd': 'USD', 'долл': 'USD', 'долларов': 'USD', 'доллара': 'USD', 'доллар': 'USD',
    '€': 'EUR', 'eur': 'EUR', 'евро': 'EUR',
    'usdt': 'USDT', 'ton': 'TON',
}
_FOREVER_WORDS = {'навсегда', 'бессрочно', 'forever', 'lifetime', '∞'}
_UNITS = {}
for _words, _days in (
        (('д', 'дн', 'день', 'дня', 'дней', 'сут', 'суток', 'd', 'day', 'days'), 1),
        (('нед', 'неделя', 'недели', 'недель', 'неделю', 'w', 'wk', 'week', 'weeks'), 7),
        (('мес', 'месяц', 'месяца', 'месяцев', 'm', 'mo', 'month', 'months'), 30),
        (('г', 'год', 'года', 'лет', 'y', 'year', 'years'), 365)):
    for _word in _words:
        _UNITS[_word] = _days


def join_link(chat_id: int) -> str:
    """The link to the group's page in the bot, for those who want in."""
    return f"https://t.me/{constants.bot_nickname}?start=j_{chat_id}"


# Plans

def default_currency(language_code: str | None) -> str:
    return 'RUB' if (language_code or '').lower().startswith('ru') else 'USD'


def _tokens(line: str) -> list[str]:
    line = line.lower().replace(',', '.')
    line = re.sub(r'[–—:=/|]', ' ', line)
    line = re.sub(r'(?<=\d)-|-(?=\d)', ' ', line)
    # "1000₽", "10$", "$10", "30д": numbers apart from words and symbols
    line = re.sub(r'(?<=\d)(?=[^\d\s.])|(?<=[^\d\s.])(?=\d)', ' ', line)
    return [token.strip('.') for token in line.split() if token.strip('.')]


def parse_plan(line: str, currency: str) -> dict | None:
    """One price line, e.g. "30 days 1000 ₽", or the price first with its currency: "$10 month"; None when it is
    not one."""
    tokens = _tokens(line)
    if not tokens:
        return None
    # The price first, marked by its currency ("$10 month", "1000 ₽ 30 days"): move it to the end
    if tokens[0] in _CURRENCY_WORDS and len(tokens) > 2:
        tokens = tokens[2:] + tokens[:2]
    elif len(tokens) > 2 and tokens[1] in _CURRENCY_WORDS and re.fullmatch(r'\d+(\.\d+)?', tokens[0]):
        tokens = tokens[2:] + tokens[:2]

    # The term: a number of days, weeks, months, or "forever"; a unit alone means one ("месяц 500")
    if tokens[0] in _FOREVER_WORDS:
        days, tokens = 0, tokens[1:]
    elif tokens[0].isdigit():
        days, tokens = int(tokens[0]), tokens[1:]
        if tokens and tokens[0] in _UNITS:
            days, tokens = days * _UNITS[tokens[0]], tokens[1:]
    elif tokens[0] in _UNITS:
        days, tokens = _UNITS[tokens[0]], tokens[1:]
    else:
        return None
    if days < 0 or days > MAX_DAYS:
        return None

    # The price, with a currency before or after it; "1 000" is a thousand
    chosen = None
    if tokens and tokens[0] in _CURRENCY_WORDS:
        chosen, tokens = _CURRENCY_WORDS[tokens[0]], tokens[1:]
    number = []
    while tokens and re.fullmatch(r'\d+(\.\d+)?', tokens[0]) and (not number or re.fullmatch(r'\d{3}', tokens[0])):
        number.append(tokens.pop(0))
    if not number:
        return None
    try:
        amount = Decimal(''.join(number))
    except InvalidOperation:
        return None
    if tokens and tokens[0] in _CURRENCY_WORDS:
        chosen, tokens = _CURRENCY_WORDS[tokens[0]], tokens[1:]
    if tokens or amount <= 0 or amount > MAX_AMOUNT:
        return None
    return {'days': days, 'amount': _amount_text(amount), 'currency': chosen or currency}


def parse_plans(text: str, currency: str) -> tuple[list[dict], list[str]]:
    """Plans from the owner's message, and the lines that are not prices. One currency for all: the first one
    named, else `currency`."""
    plans, bad = [], []
    for line in (text or '').splitlines():
        if not line.strip():
            continue
        plan = parse_plan(line, currency)
        if plan is None:
            bad.append(line.strip())
        else:
            plans.append((plan, line))
    named = next((plan['currency'] for plan, line in plans
                  if any(word in _CURRENCY_WORDS for word in _tokens(line))), currency)
    result = {}
    for plan, _ in plans:
        result[plan['days']] = {**plan, 'currency': named}
    ordered = sorted(result.values(), key=lambda plan: (plan['days'] == 0, plan['days']))
    return ordered[:MAX_PLANS], bad


def plans_of(chat: dict) -> list[dict]:
    plans = chat.get('access_plans')
    if isinstance(plans, str):
        try:
            plans = json.loads(plans)
        except ValueError:
            return []
    return plans if isinstance(plans, list) else []


def plan_for(chat: dict, days: int) -> dict | None:
    return next((plan for plan in plans_of(chat) if plan['days'] == days), None)


def _amount_text(amount: Decimal) -> str:
    text = format(amount.normalize(), 'f')
    return text


def format_amount(amount: str | Decimal, currency: str) -> str:
    value = Decimal(str(amount))
    whole, _, fraction = format(value.normalize(), 'f').partition('.')
    digits = f'{int(whole):,}'.replace(',', ' ')
    number = digits + (f'.{fraction}' if fraction else '')
    style = CURRENCIES.get(currency, {'symbol': currency, 'before': False})
    return f"{style['symbol']}{number}" if style['before'] else f"{number} {style['symbol']}"


def days_text(days: int, language_code: str | None) -> str:
    """"30 дней", "1 day", "навсегда"."""
    if not days:
        return localization.get_message(['access', 'term', 'forever'], language_code)
    if (language_code or '').lower().startswith('ru'):
        if days % 10 == 1 and days % 100 != 11:
            form = 'one'
        elif days % 10 in (2, 3, 4) and days % 100 not in (12, 13, 14):
            form = 'few'
        else:
            form = 'many'
    else:
        form = 'one' if days == 1 else 'many'
    return localization.get_message(['access', 'term', form], language_code, days=days)


def plan_text(plan: dict, language_code: str | None) -> str:
    return f"{days_text(plan['days'], language_code)} – {format_amount(plan['amount'], plan['currency'])}"


# The mode members see

def effective_mode(chat: dict, owner_tariff_id: int | None) -> str:
    """Paid entry needs prices, a way to pay and a paid tariff; without them members can still ask."""
    mode = chat.get('access_mode') or 'off'
    if mode == 'paid' and (not Tariff.is_paid(owner_tariff_id) or not plans_of(chat) or not ready_to_pay(chat)):
        return 'request'
    return mode


def ready_to_pay(chat: dict) -> bool:
    """The owner's link or requisites, or a provider connected (its secret readable)."""
    provider = chat.get('access_provider') or 'link'
    if provider == 'link':
        return bool(chat.get('access_payment'))
    from pkg.service.secret_box import unseal
    if unseal(chat.get('access_secret')) is None:
        return False
    # Tribute: every term sold as one of the owner's products
    return provider != 'tribute' or all(plan.get('product_id') and plan.get('url') for plan in plans_of(chat))


def payment_url(chat: dict) -> str | None:
    """The owner's payment link, when what they gave is one."""
    payment = (chat.get('access_payment') or '').strip()
    return payment if re.fullmatch(r'https?://\S+', payment) else None


# Granting

async def grant(chat_id: int, user_service_id: str, nickname: str | None, display_name: str | None,
                days: int) -> dict | None:
    """Lets the member write: for good (days 0), or for `days` more. More time on a running term adds to it; an
    access for good stays for good."""
    current = await allowed_user_repository.get_privileges_by_chat_id(chat_id, user_service_id, nickname)
    if current is not None and current['active']:
        if current['expires_at'] is None:
            return current
        if days:
            start = max(current['expires_at'], datetime.datetime.now())
            return await allowed_user_repository.set_expiry(current['id'], start + datetime.timedelta(days=days))
    return await AllowedUser.allow(chat_id, user_service_id, nickname, display_name, days or None)


async def current_access(chat_id: int, user_service_id: str, nickname: str | None) -> dict | None:
    entry = await allowed_user_repository.get_privileges_by_chat_id(chat_id, user_service_id, nickname)
    return entry if entry is not None and entry['active'] else None


class Requests:
    create = staticmethod(access_repository.create)
    find = staticmethod(access_repository.find)
    latest = staticmethod(access_repository.latest)
    decide = staticmethod(access_repository.decide)
    update = staticmethod(access_repository.update)
    pending = staticmethod(access_repository.pending)
    pending_count = staticmethod(access_repository.pending_count)
