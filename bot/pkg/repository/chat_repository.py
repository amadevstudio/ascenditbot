from pkg.repository.database_connection import Database

db = Database()


def find(chat_id: int):
    return db.find('moderated_chats', chat_id)


def create(chat_service_id: str, user_service_id: str):
    user = db.fetchone("""
        SELECT id FROM users WHERE service_id = %s
    """, (user_service_id,))

    if user is None:
        return {"error": "user_none"}

    chat = db.fetchone("""
        SELECT id FROM moderated_chats WHERE service_id = %s
    """, (chat_service_id,))

    if chat is None:
        chat_data = {'service_id': chat_service_id}
        chat, cursor = db.insert_model('moderated_chats', chat_data, commit=False)
    else:
        user_chat = db.fetchone("""
            SELECT * FROM user_moderated_chat_connections WHERE user_id = %s AND moderated_chat_id = %s
        """, (user['id'], chat['id'],))
        if user_chat is not None:
            return {"error": "connection_exists", "connection": user_chat}

        cursor = None

    user_chat_data = {'user_id': user["id"], 'moderated_chat_id': chat["id"]}
    user_chat = db.insert_model('user_moderated_chat_connections', user_chat_data, cursor=cursor)

    return user_chat


def user_chats_count(user_id: str):
    return db.fetchone("""
        SELECT COUNT(*) FROM user_moderated_chat_connections
        WHERE user_id = %s
    """, (user_id,))['count']


def user_chats_count_by_service_id(chat_id: str):
    return db.fetchone("""
        SELECT COUNT(*) FROM user_moderated_chat_connections AS umcc
        INNER JOIN users AS u ON (u.id = umcc.user_id)
        
        WHERE u.service_id = %s
    """, (chat_id,))['count']


def user_chats(user_id: str, order_by: str, limit: int, offset: int):
    if order_by == "created_at":
        order_by = "mc.created_at"

    return db.fetchall("""
        SELECT mc.* FROM moderated_chats AS mc
        INNER JOIN user_moderated_chat_connections AS umcc ON (umcc.moderated_chat_id = mc.id)
        WHERE umcc.user_id = %s
        ORDER BY {order_field} LIMIT %s OFFSET %s
    """.format(order_field=order_by), (user_id, limit, offset,))


def user_chats_by_service_id(chat_id: str, order_by: str, limit: int, offset: int):
    if order_by == "created_at":
        order_by = "mc.created_at"

    return db.fetchall("""
        SELECT mc.* FROM moderated_chats AS mc
        INNER JOIN user_moderated_chat_connections AS umcc ON (umcc.moderated_chat_id = mc.id)
        INNER JOIN users AS u ON (u.id = umcc.user_id)
        WHERE u.service_id = %s
        ORDER BY {order_field} LIMIT %s OFFSET %s
    """.format(order_field=order_by), (chat_id, limit, offset,))


def switch_active(chat_id: int):
    return db.commit("""
        UPDATE moderated_chats SET active = NOT active WHERE id = %s
    """, (chat_id, ), returning='active')
