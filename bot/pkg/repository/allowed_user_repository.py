from pkg.repository.database_connection import Database

db = Database()


def find(allowed_user_id: int):
    return db.find('allowed_users', allowed_user_id)
