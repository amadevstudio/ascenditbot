"""Connecting a group to the user who added the bot, from either of the two updates that may say so.

Picking a group with the "Select a group" button (request_chat with the bot's rights) makes Telegram add the bot
as an admin and then share the group: the bot gets my_chat_member and a chat_shared message, close together and
in any order. Both connect the group here, one at a time per group, and only the first announces it, so the user
gets one page, not two."""
import asyncio
from collections import defaultdict

from framework.repository.storage_connection import Storage
from pkg.service.chat import Chat
from pkg.service.user import User

# The rights the bot asks for: delete what breaks the rules, mute offenders, pin the way in
BOT_RIGHTS = {'can_delete_messages': True, 'can_restrict_members': True, 'can_pin_messages': True}
# Those who may give the bot rights: admins with the same rights who can add admins
USER_RIGHTS = {**BOT_RIGHTS, 'can_promote_members': True}

_locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
_ANNOUNCED_FOR_SECONDS = 120


async def connect(chat_service_id: int | str, user_service_id: int) -> dict:
    """{'moderated_chat_id', 'new'} or {'error': ...}; the group already connected for this user is no error."""
    async with _locks[str(chat_service_id)]:
        if await User.find_by_service_id(user_service_id) is None:
            return {'error': 'not_registered'}
        result = await Chat.add(chat_service_id, user_service_id)
        existed = result.get('error') == 'connection_exists'
        if 'error' in result and not existed:
            return result
        connection = result.get('connection', result)
        await Chat.update_names(user_service_id)
        return {'moderated_chat_id': connection['moderated_chat_id'], 'new': not existed}


async def connect_soon(chat_service_id: int | str, user_service_id: int, tries: int = 3, pause: float = 1.5) -> dict:
    """The same, for chat_shared: the bot may not be an admin yet when it comes, so a few tries."""
    result = await connect(chat_service_id, user_service_id)
    for _ in range(tries - 1):
        if 'error' not in result or result['error'] not in ('not_admin', 'cant_edit_messages', 'not_member',
                                                            'not_found', 'unknown', 'unexpected'):
            break
        await asyncio.sleep(pause)
        result = await connect(chat_service_id, user_service_id)
    return result


def first_to_announce(moderated_chat_id: int, user_service_id: int) -> bool:
    """True once for a group and a user within a couple of minutes: who sends "connected" and the page."""
    key = f"group_connected:{moderated_chat_id}:{user_service_id}"
    return bool(Storage().connection.set(key, 1, nx=True, ex=_ANNOUNCED_FOR_SECONDS))
