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

    return user_chat


async def user_chats_count(user_id: str) -> int | None:
    return (await databaseExecutor.run(db.fetchone, """
        SELECT COUNT(*) FROM user_moderated_chat_connections
        WHERE user_id = %s
    """, (user_id,)))['count']


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


async def is_active_by_service_id(chat_service_id: str) -> bool:
    result = await databaseExecutor.run(db.fetchone, """
        SELECT active FROM moderated_chats WHERE service_id = %s
    """, (chat_service_id,))
    if result is None:
        return False

    return result['active']


async def switch_active(chat_id: int) -> bool:
    return (await databaseExecutor.run(db.execute_single_model, """
        UPDATE moderated_chats SET active = NOT active WHERE id = %s
    """, (chat_id,), returning='active'))['active']


async def add_to_whitelist(chat_id: int, user_nickname: str) -> ModeratedChatInterface | None:
    allowed_user = {'moderated_chat_id': chat_id, 'nickname': user_nickname}
    return await databaseExecutor.run(db.insert_model,
        'allowed_users', allowed_user, conflict_unique_fields=['moderated_chat_id', 'nickname'])


async def chat_whitelist_count(chat_id: int, search_query: str | None = None) -> int | None:
    request_params = (chat_id,)

    if search_query is not None and search_query != "":
        search_query_sql = " AND LOWER(nickname) LIKE LOWER('%%' || %s || '%%')"
        request_params += (search_query,)
    else:
        search_query_sql = ""

    return (await databaseExecutor.run(db.fetchone, """
            SELECT COUNT(*) FROM allowed_users
            WHERE moderated_chat_id = %s {search_query_sql}
        """.format(search_query_sql=search_query_sql),
        request_params))['count']


async def chat_whitelist(
        chat_id: int, search_query: str | None = None,
        order_by: Literal['nickname', 'created_at'] = 'nickname', limit: int | None = None, offset: int = 0) \
        -> List[AllowedUserInterface] | None:

    request_params = (chat_id,)

    match order_by:
        case 'created_at':
            order_by = "created_at"
        case 'nickname':
            order_by = "nickname, created_at"
        case _:
            order_by = "nickname, created_at"

    if search_query is not None and search_query != "":
        search_query_sql = " AND LOWER(nickname) LIKE LOWER('%%' || %s || '%%')"
        request_params += (search_query,)
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
