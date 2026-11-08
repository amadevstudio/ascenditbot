from typing import List, Literal

from framework.repository.database_executor import databaseExecutor
from pkg.repository.database_connection import Database, Connection
from project.types import ModeratedChatInterface, ErrorDictInterface, AllowedUserInterface, \
    UserModeratedChatConnectionInterface, UserInterface

db = Database()


class CreateErrorInterface(ErrorDictInterface, total=False):
    connection: ModeratedChatInterface


async def find(chat_id: int) -> ModeratedChatInterface:
    return await databaseExecutor.run(db.find_model, 'moderated_chats', {'id': chat_id})


async def find_by(fields_value: ModeratedChatInterface) -> ModeratedChatInterface:
    return await databaseExecutor.run(db.find_model, 'moderated_chats', fields_value)


async def update(chat_data: ModeratedChatInterface) -> ModeratedChatInterface:
    return await databaseExecutor.run(db.update_model, 'moderated_chats', chat_data, ['id'])


async def chat_creator(chat_id: int) -> UserInterface:
    return await databaseExecutor.run(db.fetchone, """
        SELECT u.*
        FROM users AS u
        INNER JOIN user_moderated_chat_connections AS umcc ON (umcc.user_id = u.id)
        WHERE
            umcc.moderated_chat_id = %s
            AND umcc.owner IS TRUE
    """, (chat_id,))


async def owner_tariff_id(chat_id: int) -> int | None:
    result = await databaseExecutor.run(db.fetchone, """
        SELECT utc.tariff_id
        FROM user_moderated_chat_connections AS umcc
        INNER JOIN user_tariff_connections AS utc ON (utc.user_id = umcc.user_id)
        WHERE
            umcc.moderated_chat_id = %s
            AND umcc.owner IS TRUE
        LIMIT 1
    """, (chat_id,))
    return None if result is None else result['tariff_id']


# async def chat_creator_by_service_id(chat_service_id: str) -> UserInterface:
#     return await databaseExecutor.run(db.fetchone, """
#         SELECT u.*
#         FROM users AS u
#         INNER JOIN user_moderated_chat_connections AS umcc ON (umcc.user_id = u.id)
#         INNER JOIN moderated_chats AS mc ON (mc.id = umcc.moderated_chat_id)
#         WHERE
#             mc.service_id = %s
#             AND umcc.owner IS TRUE
#     """, (chat_service_id,))


async def create(chat_service_id: str, user_service_id: str, is_owner: bool) \
        -> ModeratedChatInterface | CreateErrorInterface:
    user = await databaseExecutor.run(db.fetchone, """
        SELECT id FROM users WHERE service_id = %s
    """, (user_service_id,))

    if user is None:
        return {'error': 'user_none'}

    chat = await databaseExecutor.run(db.fetchone, """
        SELECT id FROM moderated_chats WHERE service_id = %s
    """, (chat_service_id,))

    connection: Connection
    async with db.get_connection() as connection:
        async with connection.transaction():
            if chat is None:
                chat_data = {'service_id': chat_service_id}
                chat = await databaseExecutor.run(db.insert_model, 'moderated_chats', chat_data, connection=connection)
            else:
                user_chat = await databaseExecutor.run(db.fetchone, """
                    SELECT * FROM user_moderated_chat_connections WHERE user_id = %s AND moderated_chat_id = %s
                """, (user['id'], chat['id'],))
                if user_chat is not None:
                    return {'error': 'connection_exists', 'connection': user_chat}

            user_chat_data: UserModeratedChatConnectionInterface = \
                {'user_id': user["id"], 'moderated_chat_id': chat["id"], 'owner': is_owner}
            user_chat = await databaseExecutor.run(
                db.insert_model, 'user_moderated_chat_connections', user_chat_data, connection=connection)

            await connection.execute("""
                INSERT INTO attribution_events
                    (event_key, event_type, user_id, moderated_chat_id, owner)
                VALUES ($1, 'group_connected', $2, $3, $4)
                ON CONFLICT (event_key) DO NOTHING
            """, f"group:{user_chat['id']}", user['id'], chat['id'], is_owner)

    return user_chat


async def user_chats_count(user_id: str) -> int | None:
    return (await databaseExecutor.run(db.fetchone, """
        SELECT COUNT(*) FROM user_moderated_chat_connections
        WHERE user_id = %s
    """, (int(user_id),)))['count']


async def user_chats_count_by_service_id(user_chat_id: str, search_query: str | None = None) -> int | None:
    request_params = (user_chat_id,)

    if search_query is not None and search_query != "":
        search_query_sql = " AND LOWER(mc.name) LIKE LOWER('%%' || %s || '%%')"
        request_params += (search_query,)
    else:
        search_query_sql = ""

    return (await databaseExecutor.run(db.fetchone, """
        SELECT COUNT(*) FROM user_moderated_chat_connections AS umcc
        LEFT JOIN moderated_chats AS mc ON (mc.id = umcc.moderated_chat_id)
        INNER JOIN users AS u ON (u.id = umcc.user_id)
        WHERE u.service_id = %s {search_query_sql}
    """.format(search_query_sql=search_query_sql),
        request_params))['count']


async def user_working_chats(user_id: int) -> List[ModeratedChatInterface]:
    """The user's groups the bot should be moderating now: switched on and covered by the tariff."""
    return await databaseExecutor.run(db.fetchall, """
        SELECT mc.* FROM moderated_chats AS mc
        INNER JOIN user_moderated_chat_connections AS umcc ON (umcc.moderated_chat_id = mc.id)
        WHERE umcc.user_id = %s AND mc.active AND NOT mc.disabled
        ORDER BY mc.name, mc.created_at
    """, (int(user_id),))


async def user_chats(user_id: str, order_by: str, limit: int, offset: int) -> List[ModeratedChatInterface]:
    if order_by == "created_at":
        order_by = "mc.created_at"

    return await databaseExecutor.run(db.fetchall, """
        SELECT mc.* FROM moderated_chats AS mc
        INNER JOIN user_moderated_chat_connections AS umcc ON (umcc.moderated_chat_id = mc.id)
        WHERE umcc.user_id = %s
        ORDER BY {order_field} LIMIT %s OFFSET %s
    """.format(order_field=order_by), (user_id, limit, offset,))


async def user_chats_by_service_id(
        user_chat_id: str, search_query: str | None = None,
        order_by: Literal['name', 'created_at'] = 'name', limit: int | None = None, offset: int = 0) \
        -> List[ModeratedChatInterface]:

    request_params = (user_chat_id,)

    match order_by:
        case 'created_at':
            order_by = "mc.created_at"
        case 'name':
            order_by = "mc.name, mc.created_at"
        case _:
            order_by = "mc.name, mc.created_at"

    if search_query is not None and search_query != "":
        search_query_sql = " AND LOWER(mc.name) LIKE LOWER('%%' || %s || '%%')"
        request_params += (search_query,)
    else:
        search_query_sql = ""

    if limit is not None:
        limit_sql = " LIMIT %s "
        request_params += (limit, )
    else:
        limit_sql = ""

    request_params += (offset,)

    return await databaseExecutor.run(db.fetchall, """
        SELECT mc.* FROM moderated_chats AS mc
        INNER JOIN user_moderated_chat_connections AS umcc ON (umcc.moderated_chat_id = mc.id)
        INNER JOIN users AS u ON (u.id = umcc.user_id)
        WHERE u.service_id = %s {search_query_sql}
        ORDER BY {order_field} {limit_sql} OFFSET %s
    """.format(order_field=order_by, search_query_sql=search_query_sql, limit_sql=limit_sql),
        request_params)


async def switch_active(chat_id: int) -> bool:
    return (await databaseExecutor.run(db.execute_single_model, """
        UPDATE moderated_chats SET active = NOT active WHERE id = %s
    """, (chat_id,), returning='active'))['active']


async def update_restriction_duration(chat_id: int, duration_minutes: int) -> int:
    return (await databaseExecutor.run(db.execute_single_model, """
        UPDATE moderated_chats SET restriction_duration_minutes = %s WHERE id = %s
    """, (duration_minutes, chat_id,), returning='restriction_duration_minutes'))['restriction_duration_minutes']


async def delete(chat_id: int) -> int | None:
    connection: Connection
    async with db.get_connection() as connection:
        async with connection.transaction():
            await connection.execute(
                "DELETE FROM allowed_users WHERE moderated_chat_id = $1", chat_id)
            await connection.execute(
                "DELETE FROM moderated_chat_statistics WHERE moderated_chat_id = $1", chat_id)
            await connection.execute(
                "DELETE FROM user_moderated_chat_connections WHERE moderated_chat_id = $1", chat_id)
            deleted_chat = await connection.fetchrow(
                "DELETE FROM moderated_chats WHERE id = $1 RETURNING id", chat_id)

    return None if deleted_chat is None else deleted_chat['id']


async def chat_whitelist_count(chat_id: int, search_query: str | None = None) -> int | None:
    request_params = (chat_id,)

    if search_query is not None and search_query != "":
        search_query_sql = (
            " AND (LOWER(nickname) LIKE LOWER('%%' || %s || '%%')"
            " OR LOWER(display_name) LIKE LOWER('%%' || %s || '%%') OR user_service_id = %s)")
        request_params += (search_query.lstrip('@'), search_query, search_query.strip())
    else:
        search_query_sql = ""

    return (await databaseExecutor.run(db.fetchone, """
            SELECT COUNT(*) FROM allowed_users
            WHERE moderated_chat_id = %s {search_query_sql}
        """.format(search_query_sql=search_query_sql),
        request_params))['count']


async def whitelist_summary(chat_id: int) -> dict:
    """How many on the whitelist may write, are switched off, have an access that has ended."""
    return await databaseExecutor.run(db.fetchone, """
        SELECT COUNT(*) FILTER (WHERE active AND (expires_at IS NULL OR expires_at > LOCALTIMESTAMP)) AS writing,
            COUNT(*) FILTER (WHERE NOT active AND (expires_at IS NULL OR expires_at > LOCALTIMESTAMP)) AS off,
            COUNT(*) FILTER (WHERE expires_at IS NOT NULL AND expires_at <= LOCALTIMESTAMP) AS ended
        FROM allowed_users WHERE moderated_chat_id = %s
    """, (chat_id,))


async def delete_ended(chat_id: int) -> int:
    """Takes those whose access has ended off the whitelist; how many."""
    rows = await databaseExecutor.run(db.fetchall, """
        DELETE FROM allowed_users
        WHERE moderated_chat_id = %s AND expires_at IS NOT NULL AND expires_at <= LOCALTIMESTAMP
        RETURNING id
    """, (chat_id,))
    return len(rows or [])


async def chat_whitelist(
        chat_id: int, search_query: str | None = None,
        order_by: Literal['nickname', 'created_at'] = 'nickname', limit: int | None = None, offset: int = 0) \
        -> List[AllowedUserInterface] | None:

    request_params = (chat_id,)

    # Those who may write first, then those switched off, then those whose access has ended; by name in each
    name = "LOWER(COALESCE(nickname, display_name)) NULLS LAST, user_service_id"
    match order_by:
        case 'created_at':
            order_by = "created_at"
        case _:
            order_by = (f"CASE WHEN expires_at IS NOT NULL AND expires_at <= LOCALTIMESTAMP THEN 2 "
                        f"WHEN NOT active THEN 1 ELSE 0 END, {name}, created_at")

    if search_query is not None and search_query != "":
        search_query_sql = (
            " AND (LOWER(nickname) LIKE LOWER('%%' || %s || '%%')"
            " OR LOWER(display_name) LIKE LOWER('%%' || %s || '%%') OR user_service_id = %s)")
        request_params += (search_query.lstrip('@'), search_query, search_query.strip())
    else:
        search_query_sql = ""

    if limit is not None:
        limit_sql = " LIMIT %s "
        request_params += (limit,)
    else:
        limit_sql = ""

    request_params += (offset,)

    return await databaseExecutor.run(db.fetchall, """
        SELECT * FROM allowed_users
        WHERE moderated_chat_id = %s {search_query_sql}
        ORDER BY {order_field} {limit_sql} OFFSET %s
    """.format(search_query_sql=search_query_sql, order_field=order_by, limit_sql=limit_sql),
        request_params)


async def update_settings(chat_id: int, settings: dict) -> ModeratedChatInterface | None:
    """Changes the group's own settings (who may write, the posting limit, the owner's alerts, the way in)."""
    allowed = {'everyone_can_write', 'allow_administrators', 'post_limit', 'post_limit_hours', 'owner_alerts',
               'access_mode', 'access_terms', 'access_plans', 'access_provider', 'access_payment',
               'access_secret', 'access_provider_label', 'access_hook_key'}
    assert set(settings) <= allowed, settings
    return await databaseExecutor.run(db.update_model, 'moderated_chats', {'id': chat_id, **settings})


async def count_removed(chat_id: int):
    await databaseExecutor.run(db.execute_single_model, """
        INSERT INTO moderated_chat_statistics (moderated_chat_id, day, deleted_messages_count, created_at, updated_at)
        VALUES (%s, CURRENT_DATE, 1, LOCALTIMESTAMP, LOCALTIMESTAMP)
        ON CONFLICT (moderated_chat_id, day) DO UPDATE
        SET deleted_messages_count = moderated_chat_statistics.deleted_messages_count + 1,
            updated_at = LOCALTIMESTAMP
    """, (chat_id,))


async def removed_count(chat_id: int, days: int) -> int:
    row = await databaseExecutor.run(db.fetchone, """
        SELECT COALESCE(SUM(deleted_messages_count), 0) AS removed FROM moderated_chat_statistics
        WHERE moderated_chat_id = %s AND day > CURRENT_DATE - %s::int
    """, (chat_id, days))
    return int(row['removed']) if row is not None else 0


async def managers(chat_id: int) -> list[UserInterface]:
    """The bot's users connected to the group (its owner first): who gets the group's alerts."""
    return await databaseExecutor.run(db.fetchall, """
        SELECT u.* FROM users AS u
        INNER JOIN user_moderated_chat_connections AS umcc ON umcc.user_id = u.id
        WHERE umcc.moderated_chat_id = %s
        ORDER BY umcc.owner DESC, umcc.id
    """, (chat_id,)) or []


async def is_manager(chat_id: int, user_service_id: str) -> bool:
    row = await databaseExecutor.run(db.fetchone, """
        SELECT 1 AS yes FROM user_moderated_chat_connections AS umcc
        INNER JOIN users AS u ON u.id = umcc.user_id
        WHERE umcc.moderated_chat_id = %s AND u.service_id = %s
    """, (chat_id, user_service_id))
    return row is not None


async def neighbours(chat_id: int, user_service_id: str) -> tuple[int | None, int | None]:
    """The user's groups before and after this one, in the order of their list (by name), wrapping around."""
    rows = await databaseExecutor.run(db.fetchall, """
        SELECT mc.id FROM moderated_chats AS mc
        INNER JOIN user_moderated_chat_connections AS umcc ON umcc.moderated_chat_id = mc.id
        INNER JOIN users AS u ON u.id = umcc.user_id
        WHERE u.service_id = %s
        ORDER BY mc.name, mc.created_at
    """, (user_service_id,)) or []
    ids = [row['id'] for row in rows]
    if chat_id not in ids or len(ids) < 2:
        return None, None
    index = ids.index(chat_id)
    return ids[index - 1], ids[(index + 1) % len(ids)]


async def by_hook_key(provider: str, hook_key: str) -> list[ModeratedChatInterface]:
    """The groups whose provider calls the bot at this address (pkg/service/access_providers.hook_key)."""
    return await databaseExecutor.run(db.fetchall, """
        SELECT * FROM moderated_chats WHERE access_provider = %s AND access_hook_key = %s
    """, (provider, hook_key)) or []
