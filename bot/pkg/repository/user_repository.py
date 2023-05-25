from typing import Any, TypedDict

from pkg.repository.database_connection import Database
from project.types import UserInterface

db = Database()


class NewUserRegisterResultInterface(TypedDict):
    user: UserInterface
    is_new: bool


def register_or_update_by_service_id(user_data: UserInterface, referral_service_id: str | None) \
        -> NewUserRegisterResultInterface:
    user = db.fetchone("""
        SELECT id FROM users WHERE service_id = %s
    """, (user_data["service_id"],))\

    if user is None:
        if referral_service_id is not None:
            ref_user_id = get_id_by_service_id(str(referral_service_id))
            user_data = {**user, 'ref_id': ref_user_id}
        user = db.insert_model('users', user_data)
        return {'user': user, 'is_new': True}

    user_data['id'] = user['id']
    user = db.update_model('users', user_data)
    return {'user': user, 'is_new': False}


def find_by(fields_value: dict[str, Any]) -> UserInterface:
    return db.find_model('users', fields_value)


def get_id_by_service_id(service_id: str) -> int | None:
    user = db.fetchone("""
        SELECT id FROM users WHERE service_id = %s
    """, (service_id,))

    if user is None:
        return None

    return user['id']


def update(data: UserInterface) -> UserInterface | None:
    return db.update_model('users', data, ['id'])


def update_by_service_id(service_id: str, data: UserInterface) -> UserInterface | None:
    user_id = get_id_by_service_id(service_id)
    if user_id is None:
        return None

    return update({**data, 'id': user_id})
