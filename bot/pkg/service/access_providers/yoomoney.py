"""YooMoney (ЮMoney): the owner's own wallet. The member pays by a payment page made for the request (a label
r<request id>); YooMoney tells the bot about every transfer to the wallet (HTTP notifications, set up by the
owner at https://yoomoney.ru/transfer/myservices/http-notification) and the label finds the request.

Notification (POST, form): notification_type, operation_id, amount (credited), withdraw_amount (paid by the
sender), currency (643), datetime, sender, codepro, label, test_notification, unaccepted, sign, sha1_hash
(old). sign: HMAC-SHA256, the owner's secret as the key, over the other fields sorted by name, values encoded
by RFC 3986, key=value joined by &."""
import hashlib
import hmac
import re
import urllib.parse
from decimal import Decimal, InvalidOperation

import aiohttp

from pkg.system.logger import logger

NAME = 'yoomoney'
QUICKPAY_URL = 'https://yoomoney.ru/quickpay/confirm'
SETTINGS_URL = 'https://yoomoney.ru/transfer/myservices/http-notification'
TIMEOUT = aiohttp.ClientTimeout(total=15)
_WALLET = re.compile(r'^41\d{9,18}$')


class ProviderError(Exception):
    pass


def parse_wallet(text: str) -> str | None:
    wallet = re.sub(r'\D', '', text or '')
    return wallet if _WALLET.match(wallet) else None


def supports(currency: str) -> bool:
    return currency == 'RUB'


def verify(params: dict, secret: str) -> bool:
    """The notification came from YooMoney for this secret: sign, or the old sha1_hash."""
    sign = params.get('sign')
    if sign:
        signed = '&'.join(f"{key}={urllib.parse.quote(str(value), safe='')}"
                          for key, value in sorted(params.items()) if key != 'sign')
        expected = hmac.new(secret.encode(), signed.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, sign.lower())
    old = params.get('sha1_hash')
    if old:
        fields = [params.get(name, '') for name in (
            'notification_type', 'operation_id', 'amount', 'currency', 'datetime', 'sender', 'codepro')]
        line = '&'.join(fields + [secret, params.get('label', '')])
        return hmac.compare_digest(hashlib.sha1(line.encode()).hexdigest(), old.lower())
    return False


def paid_amount(params: dict) -> Decimal:
    try:
        return Decimal(str(params.get('withdraw_amount') or params.get('amount') or '0'))
    except InvalidOperation:
        return Decimal('0')


async def _post(form: dict) -> str | None:
    """The payment page YooMoney redirects the form to; the tests replace it."""
    try:
        async with aiohttp.ClientSession(timeout=TIMEOUT) as session:
            async with session.post(QUICKPAY_URL, data=form, allow_redirects=False) as response:
                return response.headers.get('Location')
    except (aiohttp.ClientError, TimeoutError) as e:
        logger.warning('YooMoney: cannot make a payment page', e)
        return None


async def payment_url(wallet: str, amount: str, label: str, title: str) -> str:
    """A page to pay `amount` rubles to the wallet by card, marked with `label`."""
    form = {'receiver': wallet, 'quickpay-form': 'button', 'paymentType': 'AC', 'sum': str(amount),
            'label': label, 'targets': title[:150]}
    url = await _post(form)
    if url and url.startswith('http'):
        return url
    # The same form as a link: YooMoney documents the form, links like it are in common use
    return QUICKPAY_URL + '?' + urllib.parse.urlencode(form)
