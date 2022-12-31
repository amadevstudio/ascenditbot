from pkg.repository.database_connection import Database
from project.types import UserInterface

db = Database()


def register_or_update_by_service_id(user_data: UserInterface) -> int:
    user = db.fetchone("""
        SELECT id FROM users WHERE service_id = %s
    """, (user_data["service_id"],))

    if user is None:
        user = db.insert_model('users', user_data)
        return user['id']

    user_data['id'] = user['id']
    user = db.update_model('users', user_data)

    return user['id']


def get_id_by_service_id(service_id: str) -> int | None:
    user = db.fetchone("""
        SELECT id FROM users WHERE service_id = %s
    """, (service_id,))

    if user is None:
        return None

    return user['id']
