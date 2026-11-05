"""Tribute (tribute.tg): the owner sells access as Tribute digital products, one per term; the bot maps each of
the owner's terms to a product. Tribute calls the bot about every purchase (new_digital_product, with the
buyer's Telegram id), at the webhook address the owner sets in Tribute (Settings, API Keys).

API: https://tribute.tg/api/v1, the key in the header Api-Key. Webhooks: JSON {"name", "created_at",
"sent_at", "payload"}, signed in the header trbt-signature: HMAC-SHA256 of the body with the API key (the
encoding is not documented: hex or base64 are both accepted)."""
import base64
import hashlib
import hmac

import aiohttp

from pkg.system.logger import logger

NAME = 'tribute'
BASE_URL = 'https://tribute.tg/api/v1'
TIMEOUT = aiohttp.ClientTimeout(total=15)


class ProviderError(Exception):
    pass


async def _request(api_key: str, path: str, params: dict | None = None) -> dict:
    """One API call; the tests replace it."""
    try:
        async with aiohttp.ClientSession(timeout=TIMEOUT) as session:
            async with session.get(f'{BASE_URL}{path}', params=params or {}, headers={'Api-Key': api_key}) as response:
                if response.status != 200:
                    raise ProviderError(f'{path}: HTTP {response.status}')
                return await response.json(content_type=None)
    except (aiohttp.ClientError, TimeoutError, ValueError) as e:
        raise ProviderError(f'{path}: {e}') from e


async def products(api_key: str) -> list[dict]:
    """The owner's digital products: [{'id', 'name', 'link'}]; checks the key too."""
    answer = await _request(api_key, '/products', {'type': 'digital', 'size': '100'})
    rows = answer.get('rows', []) if isinstance(answer, dict) else []
    return [{'id': row['id'], 'name': row.get('name') or str(row['id']),
             'link': row.get('link') or row.get('webLink')}
            for row in rows if row.get('status', 'approved') != 'rejected']


def verify(body: bytes, signature: str | None, api_key: str) -> bool:
    if not signature:
        return False
    digest = hmac.new(api_key.encode(), body, hashlib.sha256).digest()
    return any(hmac.compare_digest(signature.strip(), expected)
               for expected in (digest.hex(), base64.b64encode(digest).decode()))


def log_error(what: str, error: Exception):
    logger.warning(f'Tribute: {what}', error)
