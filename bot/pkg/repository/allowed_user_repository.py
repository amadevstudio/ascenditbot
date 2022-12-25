from pkg.repository.database_connection import Database

db = Database()


def find(allowed_user_id: int):
    return db.find('allowed_users', allowed_user_id)


def switch_active(chat_id: int):
    return db.commit("""
        UPDATE allowed_users SET active = NOT active WHERE id = %s
    """, (chat_id,), returning='active')
