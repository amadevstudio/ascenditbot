"""Crypto Pay (@CryptoBot): the owner's own app. The bot creates an invoice in it for the term a member picks,
and checks the invoices it waits for (getInvoices); the money stays in the owner's app. No webhook: nothing to
set up on the owner's side but the token.

API: https://pay.crypt.bot/api/<method>, the app's token in the header Crypto-Pay-API-Token, answers
{"ok": true, "result": ...} or {"ok": false, "error": {"code", "name"}}."""
import aiohttp

from pkg.system.logger import logger

NAME = 'cryptobot'
BASE_URL = 'https://pay.crypt.bot/api'
# An invoice can be paid within an hour; after two the bot stops waiting for it
INVOICE_SECONDS = 3600
FIAT = {'RUB', 'USD', 'EUR'}
ASSETS = {'USDT', 'TON'}
TIMEOUT = aiohttp.ClientTimeout(total=15)


class ProviderError(Exception):
    pass


async def _request(token: str, method: str, params: dict | None = None) -> dict | list:
    """One API call; the tests replace it."""
    try:
        async with aiohttp.ClientSession(timeout=TIMEOUT) as session:
            async with session.get(f'{BASE_URL}/{method}', params=params or {},
                                   headers={'Crypto-Pay-API-Token': token}) as response:
                answer = await response.json(content_type=None)
    except (aiohttp.ClientError, TimeoutError, ValueError) as e:
        raise ProviderError(f'{method}: {e}') from e
    if not isinstance(answer, dict) or not answer.get('ok'):
        error = (answer or {}).get('error') if isinstance(answer, dict) else None
        raise ProviderError(f'{method}: {error}')
    return answer['result']


async def connect(token: str) -> str:
    """Checks the token; the app's name to show the owner."""
    profile = await _request(token, 'getMe')
    return profile.get('name') or str(profile.get('app_id'))


async def create_invoice(token: str, plan: dict, description: str, payload: str) -> dict:
    """An invoice for the plan: in fiat (RUB, USD, EUR; paid in any coin) or in USDT or TON.
    {'external_id', 'url'}."""
    params = {'amount': str(plan['amount']), 'description': description[:1024], 'payload': payload,
              'expires_in': str(INVOICE_SECONDS), 'allow_comments': 'false'}
    if plan['currency'] in ASSETS:
        params.update({'currency_type': 'crypto', 'asset': plan['currency']})
    else:
        params.update({'currency_type': 'fiat', 'fiat': plan['currency']})
    invoice = await _request(token, 'createInvoice', params)
    return {'external_id': str(invoice['invoice_id']), 'url': invoice.get('bot_invoice_url')
            or invoice.get('mini_app_invoice_url') or invoice.get('web_app_invoice_url')}


async def statuses(token: str, external_ids: list[str]) -> dict[str, str]:
    """active, paid or expired, by invoice id."""
    result = await _request(token, 'getInvoices', {'invoice_ids': ','.join(external_ids), 'count': '1000'})
    items = result.get('items', []) if isinstance(result, dict) else result
    return {str(item['invoice_id']): item.get('status', 'active') for item in items}


def supports(currency: str) -> bool:
    return currency in FIAT or currency in ASSETS


def log_error(what: str, error: Exception):
    logger.warning(f'CryptoBot: {what}', error)
