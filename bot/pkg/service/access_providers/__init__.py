"""Payment providers that confirm a payment to the bot themselves, so that access opens without the owner.

CryptoBot is asked about its invoices (no setup on the server). YooMoney and Tribute call the bot at
constants.hooks_url, which needs nginx on the server to pass /hook/ to the payment server: until it does, they
are not offered to owners."""
import hashlib
import hmac

from pkg.config.config import environment

# YooMoney and Tribute are offered once /hook/ reaches the bot (nginx on the server)
HOOKS_ENABLED = False


def hook_key(provider: str, credential: str) -> str:
    """The key in a provider's notification address: from the owner's wallet or API key, so that the same one
    used for several groups gets the same address, and nobody can guess another owner's."""
    secret = ('ascendit hook:' + environment['TELEGRAM_BOT_TOKEN']).encode()
    return hmac.new(secret, f'{provider}:{credential}'.encode(), hashlib.sha256).hexdigest()[:24]
