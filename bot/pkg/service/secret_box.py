"""Owners' credentials of payment providers (moderated_chats.access_secret), encrypted at rest: a copy of the
database alone does not give them away. The key comes from the bot's token, so a new token makes old secrets
unreadable: the owner connects the provider again."""
import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from pkg.config.config import environment


def _box() -> Fernet:
    key = hashlib.sha256(('ascendit access secret:' + environment['TELEGRAM_BOT_TOKEN']).encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key))


def seal(secret: str) -> str:
    return _box().encrypt(secret.encode()).decode()


def unseal(sealed: str | None) -> str | None:
    if not sealed:
        return None
    try:
        return _box().decrypt(sealed.encode()).decode()
    except (InvalidToken, ValueError):
        return None
