"""Requests to get into a group through the bot (access_requests): asked for free, "I paid" by the owner's link,
paid through a provider. One open (pending) request per member and group."""
from framework.repository.database_executor import databaseExecutor
from pkg.repository.database_connection import Database

db = Database()

_COLUMNS = ('moderated_chat_id', 'user_service_id', 'nickname', 'display_name', 'language_code', 'kind', 'days',
            'amount', 'currency', 'provider', 'external_id')


async def create(request: dict) -> dict | None:
    """A new pending request; None when the member already has one open for the group."""
    values = [request.get(column) for column in _COLUMNS]
    return await databaseExecutor.run(db.execute_single_model, f"""
        INSERT INTO access_requests ({', '.join(_COLUMNS)}, status, created_at, updated_at)
        VALUES ({', '.join(['%s'] * len(_COLUMNS))}, 'pending', LOCALTIMESTAMP, LOCALTIMESTAMP)
        ON CONFLICT (moderated_chat_id, user_service_id) WHERE status = 'pending' DO NOTHING
    """, tuple(values), returning='*')


async def find(request_id: int) -> dict | None:
    return await databaseExecutor.run(db.fetchone, "SELECT * FROM access_requests WHERE id = %s", (request_id,))


async def latest(chat_id: int, user_service_id: str) -> dict | None:
    return await databaseExecutor.run(db.fetchone, """
        SELECT * FROM access_requests WHERE moderated_chat_id = %s AND user_service_id = %s
        ORDER BY id DESC LIMIT 1
    """, (chat_id, user_service_id))


async def decide(request_id: int, status: str, decided_by: str | None) -> dict | None:
    """Approves or rejects a pending request; None when someone has decided it already."""
    return await databaseExecutor.run(db.execute_single_model, """
        UPDATE access_requests
        SET status = %s, decided_by = %s, decided_at = LOCALTIMESTAMP, updated_at = LOCALTIMESTAMP
        WHERE id = %s AND status = 'pending'
    """, (status, decided_by, request_id), returning='*')


async def update(request_id: int, fields: dict) -> dict | None:
    assert set(fields) <= {'days', 'amount', 'currency', 'kind', 'reminded_at', 'external_id', 'pay_url'}, fields
    sets = ', '.join(f'{name} = %s' for name in fields)
    return await databaseExecutor.run(db.execute_single_model, f"""
        UPDATE access_requests SET {sets}, updated_at = LOCALTIMESTAMP WHERE id = %s
    """, (*fields.values(), request_id), returning='*')


async def pending(chat_id: int, limit: int = 10) -> list[dict]:
    return await databaseExecutor.run(db.fetchall, """
        SELECT * FROM access_requests WHERE moderated_chat_id = %s AND status = 'pending'
        ORDER BY id LIMIT %s
    """, (chat_id, limit)) or []


async def pending_count(chat_id: int) -> int:
    return await databaseExecutor.run(db.fetchval, """
        SELECT COUNT(*) FROM access_requests WHERE moderated_chat_id = %s AND status = 'pending'
    """, (chat_id,)) or 0


async def waiting_payments(providers: tuple[str, ...], request_id: int | None = None) -> list[dict]:
    """Requests waiting for a provider's payment (all, or one), with their group's provider settings."""
    return await databaseExecutor.run(db.fetchall, """
        SELECT ar.*, mc.access_secret, mc.access_provider, mc.service_id AS chat_service_id
        FROM access_requests AS ar
        INNER JOIN moderated_chats AS mc ON mc.id = ar.moderated_chat_id
        WHERE ar.status = 'pending' AND ar.kind = 'paid_auto' AND ar.provider = ANY(%s)
            AND ar.external_id IS NOT NULL AND (%s::bigint IS NULL OR ar.id = %s)
        ORDER BY ar.id
        LIMIT 1000
    """, (list(providers), request_id, request_id)) or []


async def find_by_external(provider: str, external_id: str) -> dict | None:
    return await databaseExecutor.run(db.fetchone, """
        SELECT * FROM access_requests WHERE provider = %s AND external_id = %s
    """, (provider, external_id))
