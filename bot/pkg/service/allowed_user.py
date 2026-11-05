import datetime
import re
import typing

from pkg.repository import allowed_user_repository
from pkg.service.service import Service
from project.types import AllowedUserInterface


def term_end(days: int | None) -> datetime.datetime | None:
    """The end of a timed access of `days` from now; None (0 or None days) for good."""
    return datetime.datetime.now() + datetime.timedelta(days=days) if days else None


class AllowedUser(Service):
    @staticmethod
    async def find(allowed_user_id: int) -> AllowedUserInterface | None:
        return await allowed_user_repository.find(allowed_user_id)

    @staticmethod
    async def switch_active(allowed_user_id: int) -> bool | None:
        return await allowed_user_repository.switch_active(allowed_user_id)

    @staticmethod
    async def delete(allowed_user_id: int) -> int | None:
        return await allowed_user_repository.delete(allowed_user_id)

    @staticmethod
    async def allow(chat_id: int, user_service_id: str | None = None, nickname: str | None = None,
                    display_name: str | None = None, days: int | None = None) -> AllowedUserInterface | None:
        """Puts a member on the group's whitelist by id and/or nickname, for good or for `days`."""
        if not user_service_id and not nickname:
            return None
        return await allowed_user_repository.allow(
            chat_id, user_service_id=user_service_id, nickname=nickname.lstrip('@') if nickname else None,
            display_name=display_name, expires_at=term_end(days))

    @staticmethod
    async def disallow(chat_id: int, user_service_id: str | None = None, nickname: str | None = None) -> int:
        return await allowed_user_repository.disallow(chat_id, user_service_id, nickname)

    @staticmethod
    async def set_term(allowed_user_id: int, days: int | None) -> AllowedUserInterface | None:
        return await allowed_user_repository.set_expiry(allowed_user_id, term_end(days))


_MEMBER_LINK = re.compile(r'^(?:https?://)?(?:t\.me|telegram\.me)/([A-Za-z0-9_]{4,32})/?$')
_NICKNAME = re.compile(r'^@?([A-Za-z0-9_]{4,32})$')
_TERM = re.compile(r'^(\d{1,3})\s*(?:d|д|дн|day|days)$', re.IGNORECASE)


class Member(typing.TypedDict, total=False):
    user_service_id: str | None
    nickname: str | None
    display_name: str | None


def full_name(user) -> str:
    return ' '.join(part for part in (user.first_name, user.last_name) if part)


def parse_member_words(text: str) -> tuple[list[Member], list[str]]:
    """@nicknames, t.me links and numeric ids in a text; also the words that are none of these."""
    members, unknown = [], []
    for word in text.replace(',', ' ').split():
        if word.isdigit():
            members.append({'user_service_id': word})
        elif (match := _MEMBER_LINK.match(word) or _NICKNAME.match(word)) is not None:
            members.append({'nickname': match.group(1)})
        else:
            unknown.append(word)
    return members, unknown


def parse_term(words: list[str]) -> tuple[int | None, list[str]]:
    """A term like 7d or 30д among the words of a command: its days and the other words."""
    days, rest = None, []
    for word in words:
        match = _TERM.match(word)
        if match is not None and days is None:
            days = int(match.group(1))
        else:
            rest.append(word)
    return days, rest


def parse_members(message) -> tuple[list[Member], list[str], int | None]:
    """Who the owner means: people picked with the contacts button, the sender of a forwarded message, or
    @nicknames, t.me links and numeric ids in the text. Also the words that are none of these, and the term
    (7d) when the text has one."""
    if message.users_shared is not None:
        return [{'user_service_id': str(user.user_id), 'nickname': user.username,
                 'display_name': ' '.join(p for p in (user.first_name, user.last_name) if p) or None}
                for user in message.users_shared.users], [], None

    origin = message.forward_origin
    if origin is not None:
        sender = getattr(origin, 'sender_user', None)
        if sender is not None and not sender.is_bot:
            return [{'user_service_id': str(sender.id), 'nickname': sender.username,
                     'display_name': full_name(sender)}], [], None
        # The sender hid their account in forwards: only their name is known, which cannot be matched
        return [], [getattr(origin, 'sender_user_name', None) or '?'], None

    days, words = parse_term((message.text or '').split())
    members, unknown = parse_member_words(' '.join(words))
    return members, unknown, days
