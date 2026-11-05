import datetime

from framework.repository.database_executor import databaseExecutor
from pkg.repository.database_connection import Database
from project.types import AllowedUserInterface

db = Database()

# A whitelist entry matches a member by Telegram id, or by nickname (any case) when the id is not known yet
_MATCH = """
    (
        (%s::text IS NOT NULL AND au.user_service_id = %s)
        OR (%s::text IS NOT NULL AND LOWER(au.nickname) = LOWER(%s))
    )
"""


def _match_params(user_service_id: str | None, nickname: str | None) -> tuple:
    return user_service_id, user_service_id, nickname, nickname


async def find(allowed_user_id: int) -> AllowedUserInterface | None:
    return await databaseExecutor.run(db.find_model, 'allowed_users', {'id': allowed_user_id})


async def switch_active(allowed_user_id: int) -> bool | None:
    return (await databaseExecutor.run(db.execute_single_model, """
        UPDATE allowed_users SET active = NOT active WHERE id = %s
    """, (allowed_user_id,), returning='active'))['active']


async def delete(allowed_user_id) -> int | None:
    return await databaseExecutor.run(db.delete_model, 'allowed_users', {'id': allowed_user_id})


async def get_privileges(
        chat_service_id: str, user_service_id: str | None, nickname: str | None) -> AllowedUserInterface | None:
    """The member's entry in the group's whitelist that has not run out, the one by id first."""
    return await databaseExecutor.run(db.fetchone, f"""
        SELECT au.id, au.active, au.nickname, au.user_service_id, au.expires_at, au.moderated_chat_id
        FROM allowed_users AS au
        INNER JOIN moderated_chats AS mc ON au.moderated_chat_id = mc.id
        WHERE mc.service_id = %s AND {_MATCH}
            AND (au.expires_at IS NULL OR au.expires_at > LOCALTIMESTAMP)
        ORDER BY (au.user_service_id IS NOT NULL AND au.user_service_id = %s) DESC, au.active DESC
        LIMIT 1
    """, (chat_service_id, *_match_params(user_service_id, nickname), user_service_id))


async def get_privileges_by_chat_id(
        chat_id: int, user_service_id: str | None, nickname: str | None) -> AllowedUserInterface | None:
    """The same as get_privileges, by the group's id in the bot."""
    return await databaseExecutor.run(db.fetchone, f"""
        SELECT au.id, au.active, au.nickname, au.user_service_id, au.expires_at, au.moderated_chat_id
        FROM allowed_users AS au
        WHERE au.moderated_chat_id = %s AND {_MATCH}
            AND (au.expires_at IS NULL OR au.expires_at > LOCALTIMESTAMP)
        ORDER BY (au.user_service_id IS NOT NULL AND au.user_service_id = %s) DESC, au.active DESC
        LIMIT 1
    """, (chat_id, *_match_params(user_service_id, nickname), user_service_id))


async def remember_member(allowed_user_id: int, user_service_id: str, nickname: str | None, display_name: str):
    """Ties an entry found by nickname to the member's id (so a new username keeps access) and refreshes the
    names shown in the whitelist, unless another entry of the group already has them."""
    await databaseExecutor.run(db.execute_single_model, """
        UPDATE allowed_users AS au
        SET user_service_id = COALESCE(au.user_service_id, %s),
            display_name = %s,
            nickname = CASE
                WHEN %s::text IS NULL OR EXISTS (
                    SELECT 1 FROM allowed_users AS other
                    WHERE other.moderated_chat_id = au.moderated_chat_id AND other.id != au.id
                        AND LOWER(other.nickname) = LOWER(%s))
                THEN au.nickname ELSE %s END
        WHERE au.id = %s
            AND (au.user_service_id IS NOT NULL OR NOT EXISTS (
                SELECT 1 FROM allowed_users AS other
                WHERE other.moderated_chat_id = au.moderated_chat_id AND other.user_service_id = %s))
    """, (user_service_id, display_name, nickname, nickname, nickname, allowed_user_id, user_service_id))


async def allow(
        chat_id: int, user_service_id: str | None = None, nickname: str | None = None,
        display_name: str | None = None, expires_at: datetime.datetime | None = None) -> AllowedUserInterface:
    """Puts a member on the group's whitelist, by id, by nickname or both, until `expires_at` (None: for good).
    An existing entry of the member is switched on and gets the new term instead of a second one."""
    # The unique indexes on (group, id) and (group, nickname) keep a race from making two entries
    existing = await databaseExecutor.run(db.fetchone, f"""
        SELECT au.id FROM allowed_users AS au
        WHERE au.moderated_chat_id = %s AND {_MATCH}
        ORDER BY (au.user_service_id IS NOT NULL AND au.user_service_id = %s) DESC
        LIMIT 1
    """, (chat_id, *_match_params(user_service_id, nickname), user_service_id))

    if existing is None:
        return await databaseExecutor.run(db.insert_model, 'allowed_users', {
            'moderated_chat_id': chat_id, 'nickname': nickname, 'user_service_id': user_service_id,
            'display_name': display_name, 'expires_at': expires_at,
        })

    return await databaseExecutor.run(db.execute_single_model, """
        UPDATE allowed_users AS au
        SET active = TRUE, expires_at = %s, expiry_notice = 0, updated_at = LOCALTIMESTAMP,
            user_service_id = COALESCE(au.user_service_id, %s),
            display_name = COALESCE(%s, au.display_name),
            nickname = COALESCE(au.nickname, %s)
        WHERE au.id = %s
    """, (expires_at, user_service_id, display_name, nickname, existing['id']), returning='*')


async def disallow(chat_id: int, user_service_id: str | None = None, nickname: str | None = None) -> int:
    """Removes the member from the group's whitelist; how many entries went."""
    rows = await databaseExecutor.run(db.fetchall, f"""
        DELETE FROM allowed_users AS au
        WHERE au.moderated_chat_id = %s AND {_MATCH}
        RETURNING au.id
    """, (chat_id, *_match_params(user_service_id, nickname)))
    return len(rows or [])


async def set_expiry(allowed_user_id: int, expires_at: datetime.datetime | None) -> AllowedUserInterface | None:
    return await databaseExecutor.run(db.execute_single_model, """
        UPDATE allowed_users SET expires_at = %s, expiry_notice = 0, active = TRUE, updated_at = LOCALTIMESTAMP
        WHERE id = %s
    """, (expires_at, allowed_user_id), returning='*')


async def expiring(expiry_notice: int, until: datetime.datetime) -> list[dict]:
    """Timed entries that run out before `until` and whose owners have not been told at this stage yet,
    with what the message to the owners needs."""
    return await databaseExecutor.run(db.fetchall, """
        SELECT au.id, au.nickname, au.display_name, au.user_service_id, au.expires_at,
            mc.id AS chat_id, mc.name AS chat_name, mc.access_mode
        FROM allowed_users AS au
        INNER JOIN moderated_chats AS mc ON mc.id = au.moderated_chat_id
        WHERE au.expires_at IS NOT NULL AND au.expires_at <= %s AND au.expiry_notice < %s AND au.active IS TRUE
        ORDER BY au.expires_at
        LIMIT 500
    """, (until, expiry_notice)) or []


async def mark_expiry_notice(allowed_user_id: int, expiry_notice: int):
    await databaseExecutor.run(db.execute_single_model, """
        UPDATE allowed_users SET expiry_notice = %s WHERE id = %s
    """, (expiry_notice, allowed_user_id))
