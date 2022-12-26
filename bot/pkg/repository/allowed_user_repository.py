from pkg.repository.database_connection import Database

db = Database()


def find(allowed_user_id: int) -> dict | None:
    return db.find('allowed_users', allowed_user_id)


def switch_active(allowed_user_id: int) -> bool | None:
    return db.commit("""
        UPDATE allowed_users SET active = NOT active WHERE id = %s
    """, (allowed_user_id,), returning='active')


def delete(allowed_user_id) -> int | None:
    return db.delete('allowed_users', allowed_user_id)