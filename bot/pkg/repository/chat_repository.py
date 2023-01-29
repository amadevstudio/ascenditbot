from typing import List, Any

from pkg.repository.database_connection import Database
from project.types import ModeratedChatInterface, ErrorDictInterface, AllowedUserInterface, \
    UserModeratedChatConnectionInterface, UserInterface

db = Database()


class CreateErrorInterface(ErrorDictInterface, total=False):
    connection: ModeratedChatInterface


def find(chat_id: int) -> ModeratedChatInterface:
    return db.find_model('moderated_chats', {'id': chat_id})


def find_by(fields_value: ModeratedChatInterface) -> ModeratedChatInterface:
    return db.find_model('moderated_chats', fields_value)


def chat_creator(chat_id: int) -> UserInterface:
    return db.fetchone("""
        SELECT u.*
        FROM users AS u
        INNER JOIN user_moderated_chat_connections AS umcc ON (umcc.user_id = u.id)
        WHERE
            umcc.moderated_chat_id = %s
            AND umcc.owner IS TRUE
    """, (chat_id,))


def chat_creator_by_service_id(chat_service_id: str) -> UserInterface:
    return db.fetchone("""
        SELECT u.*
        FROM users AS u
        INNER JOIN user_moderated_chat_connections AS umcc ON (umcc.user_id = u.id)
        INNER JOIN moderated_chats AS mc ON (mc.id = umcc.moderated_chat_id)
        WHERE
            mc.service_id = %s
            AND umcc.owner IS TRUE
    """, (chat_service_id,))


def create(chat_service_id: str, user_service_id: str, is_owner: bool) -> ModeratedChatInterface | CreateErrorInterface:
    user = db.fetchone("""
        SELECT id FROM users WHERE service_id = %s
    """, (user_service_id,))

    if user is None:
        return {'error': 'user_none'}

    chat = db.fetchone("""
        SELECT id FROM moderated_chats WHERE service_id = %s
    """, (chat_service_id,))

    if chat is None:
        chat_data = {'service_id': chat_service_id}
        cursor = db.build_cursor()
        chat = db.insert_model('moderated_chats', chat_data, commit=False, cursor=cursor)
    else:
        user_chat = db.fetchone("""
            SELECT * FROM user_moderated_chat_connections WHERE user_id = %s AND moderated_chat_id = %s
        """, (user['id'], chat['id'],))
        if user_chat is not None:
            return {'error': 'connection_exists', 'connection': user_chat}

        cursor = None

    user_chat_data: UserModeratedChatConnectionInterface = \
        {'user_id': user["id"], 'moderated_chat_id': chat["id"], 'owner': is_owner}
    user_chat = db.insert_model('user_moderated_chat_connections', user_chat_data, cursor=cursor)

    return user_chat


def user_chats_count(user_id: str) -> int | None:
    return db.fetchone("""
        SELECT COUNT(*) FROM user_moderated_chat_connections
        WHERE user_id = %s
    """, (user_id,))['count']


def user_chats_count_by_service_id(user_chat_id: str) -> int | None:
    return db.fetchone("""
        SELECT COUNT(*) FROM user_moderated_chat_connections AS umcc
        INNER JOIN users AS u ON (u.id = umcc.user_id)
        
        WHERE u.service_id = %s
    """, (user_chat_id,))['count']


def user_chats(user_id: str, order_by: str, limit: int, offset: int) -> List[ModeratedChatInterface]:
    if order_by == "created_at":
        order_by = "mc.created_at"

    return db.fetchall("""
        SELECT mc.* FROM moderated_chats AS mc
        INNER JOIN user_moderated_chat_connections AS umcc ON (umcc.moderated_chat_id = mc.id)
        WHERE umcc.user_id = %s
        ORDER BY {order_field} LIMIT %s OFFSET %s
    """.format(order_field=order_by), (user_id, limit, offset,))


def user_chats_by_service_id(user_chat_id: str, order_by: str, limit: int, offset: int) -> List[ModeratedChatInterface]:
    if order_by == "created_at":
        order_by = "mc.created_at"

    return db.fetchall("""
        SELECT mc.* FROM moderated_chats AS mc
        INNER JOIN user_moderated_chat_connections AS umcc ON (umcc.moderated_chat_id = mc.id)
        INNER JOIN users AS u ON (u.id = umcc.user_id)
        WHERE u.service_id = %s
        ORDER BY {order_field} LIMIT %s OFFSET %s
    """.format(order_field=order_by), (user_chat_id, limit, offset,))


def is_active_by_service_id(chat_service_id: str) -> bool:
    result = db.fetchone("""
        SELECT active FROM moderated_chats WHERE service_id = %s
    """, (chat_service_id,))
    if result is None:
        return False

    return result['active']


def switch_active(chat_id: int) -> bool:
    return db.execute("""
        UPDATE moderated_chats SET active = NOT active WHERE id = %s
    """, (chat_id,), commit=True, returning='active')['active']


def add_to_whitelist(chat_id: int, user_nickname: str) -> ModeratedChatInterface | None:
    allowed_user = {'moderated_chat_id': chat_id, 'nickname': user_nickname}
    return db.insert_model(
        'allowed_users', allowed_user, conflict_unique_fields=['moderated_chat_id', 'nickname'])


def chat_whitelist_count(chat_id: int) -> int | None:
    return db.fetchone("""
            SELECT COUNT(*) FROM allowed_users
            WHERE moderated_chat_id = %s
        """, (chat_id,))['count']


def chat_whitelist(chat_id: int, order_by: str, limit: int, offset: int) -> List[AllowedUserInterface] | None:
    return db.fetchall("""
        SELECT * FROM allowed_users
        WHERE moderated_chat_id = %s
        ORDER BY {order_field} LIMIT %s OFFSET %s
    """.format(order_field=order_by), (chat_id, limit, offset,))
