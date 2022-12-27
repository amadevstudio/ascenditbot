from pkg.repository.database_connection import Database
from project.types import AllowedUserInterface

db = Database()


def find(allowed_user_id: int) -> AllowedUserInterface | None:
    return db.find('allowed_users', allowed_user_id)


def switch_active(allowed_user_id: int) -> bool | None:
    return db.commit("""
        UPDATE allowed_users SET active = NOT active WHERE id = %s
    """, (allowed_user_id,), returning='active')


def delete(allowed_user_id) -> int | None:
    return db.delete('allowed_users', allowed_user_id)


def get_privileges(nickname: str, chat_service_id: str) -> AllowedUserInterface | None:
    return db.fetchone("""
        SELECT au.active, au.images_allowed, au.links_allowed,
            au.period_quantity, au.period_type, au.period_quantity_left, au.ban_expiration_date
        FROM allowed_users AS au
        INNER JOIN moderated_chats AS mc ON au.moderated_chat_id = mc.id
        WHERE mc.service_id = %s AND au.nickname = %s
    """, (chat_service_id, nickname,))
