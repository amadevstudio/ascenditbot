from pkg.repository.database_connection import Database

db = Database()


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
