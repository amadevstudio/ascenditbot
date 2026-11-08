from typing import Any, TypedDict

from framework.repository.database_executor import databaseExecutor
from pkg.repository.database_connection import Database
from project.types import UserInterface

db = Database()


class NewUserRegisterResultInterface(TypedDict):
    user: UserInterface
    is_new: bool


async def register_or_update_by_service_id(
        user_data: UserInterface, referral_service_id: str | None,
        source: str | None = None, start_event_key: str | None = None,
) \
        -> NewUserRegisterResultInterface:
    """`source`, the tag of the link (pkg/service/attribution.py): a new user's first source, a touch for anyone."""
    async with db.get_connection() as connection:
        async with connection.transaction():
            # Serialise simultaneous first updates for this Telegram account, including when no row exists yet.
            await connection.execute("SELECT pg_advisory_xact_lock(hashtext($1))", user_data['service_id'])
            existing = await connection.fetchrow(
                "SELECT id FROM users WHERE service_id = $1 FOR UPDATE", user_data['service_id'])

            if existing is None:
                insert_data = dict(user_data)
                if referral_service_id is not None:
                    referrer = await connection.fetchrow(
                        "SELECT id FROM users WHERE service_id = $1", str(referral_service_id))
                    insert_data['ref_id'] = referrer['id'] if referrer else None
                insert_data['first_source'] = source or 'direct_unknown'
                user = await databaseExecutor.run(db.insert_model, 'users', insert_data, connection=connection)
                is_new = True
            else:
                update_data = dict(user_data, id=existing['id'])
                user = await databaseExecutor.run(db.update_model, 'users', update_data, connection=connection)
                is_new = False

            if start_event_key is not None and source is not None:
                await connection.execute("""
                    INSERT INTO attribution_events
                        (event_key, event_type, user_id, touch_source, is_new_user)
                    VALUES ($1, 'bot_start', $2, $3, $4)
                    ON CONFLICT (event_key) DO NOTHING
                """, start_event_key, user['id'], source, is_new)

    return {'user': user, 'is_new': is_new}


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
