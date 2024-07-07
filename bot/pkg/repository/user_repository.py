from typing import Any, TypedDict

from framework.repository.database_executor import databaseExecutor
from pkg.repository.database_connection import Database
from project.types import UserInterface

db = Database()


class NewUserRegisterResultInterface(TypedDict):
    user: UserInterface
    is_new: bool


async def register_or_update_by_service_id(user_data: UserInterface, referral_service_id: str | None) \
        -> NewUserRegisterResultInterface:
    user = await databaseExecutor.run(db.fetchone, """
        SELECT id FROM users WHERE service_id = %s
    """, (user_data["service_id"],))

    if user is None:
        if referral_service_id is not None:
            ref_user_id = await get_id_by_service_id(str(referral_service_id))
            user_data = {**user, 'ref_id': ref_user_id}
        user = await databaseExecutor.run(db.insert_model, 'users', user_data)
        return {'user': user, 'is_new': True}

    user_data['id'] = user['id']
    user = await databaseExecutor.run(db.update_model, 'users', user_data)
    return {'user': user, 'is_new': False}


async def find_by(fields_value: dict[str, Any]) -> UserInterface | None:
    return await databaseExecutor.run(db.find_model, 'users', fields_value)


async def get_id_by_service_id(service_id: str) -> int | None:
    user = await databaseExecutor.run(db.fetchone, """
        SELECT id FROM users WHERE service_id = %s
    """, (service_id,))

    if user is None:
        return None

    return user['id']


async def update(data: UserInterface) -> UserInterface | None:
    return await databaseExecutor.run(db.update_model, 'users', data, ['id'])


async def update_by_service_id(service_id: str, data: UserInterface) -> UserInterface | None:
    user_id = await get_id_by_service_id(service_id)
    if user_id is None:
        return None

    return await update({**data, 'id': user_id})
