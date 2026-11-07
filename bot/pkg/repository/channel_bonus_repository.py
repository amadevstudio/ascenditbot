"""Channels to subscribe to for bonus days, and who took the bonus (migrator 20261112120000_channel_bonus)."""
from framework.repository.database_executor import databaseExecutor
from pkg.repository.database_connection import Database

db = Database()


async def channels() -> list[dict]:
    return await databaseExecutor.run(db.fetchall, """
        SELECT pc.*,
            (SELECT COUNT(*) FROM channel_bonus_claims AS c WHERE pc.service_id = ANY(c.channel_ids)) AS claimed,
            (SELECT COUNT(*) FROM channel_bonus_claims AS c
             WHERE pc.service_id = ANY(c.channel_ids) AND c.lost_at IS NOT NULL) AS lost
        FROM promo_channels AS pc
        ORDER BY pc.id
    """, ()) or []


async def add_channel(service_id: str, title: str | None, link: str | None) -> dict:
    return await databaseExecutor.run(db.fetchone, """
        INSERT INTO promo_channels (service_id, title, link) VALUES (%s, %s, %s)
        ON CONFLICT (service_id) DO UPDATE SET title = EXCLUDED.title, link = EXCLUDED.link,
            updated_at = CURRENT_TIMESTAMP
        RETURNING *
    """, (service_id, title, link))


async def update_channel(service_id: str, title: str | None, link: str | None) -> dict | None:
    return await databaseExecutor.run(db.fetchone, """
        UPDATE promo_channels SET title = %s, link = %s, updated_at = CURRENT_TIMESTAMP WHERE service_id = %s
        RETURNING *
    """, (title, link, service_id))


async def delete_channel(channel_id: int) -> dict | None:
    return await databaseExecutor.run(db.fetchone, """
        DELETE FROM promo_channels WHERE id = %s RETURNING *
    """, (int(channel_id),))


async def claim(user_id: int) -> dict | None:
    return await databaseExecutor.run(db.fetchone, """
        SELECT * FROM channel_bonus_claims WHERE user_id = %s
    """, (int(user_id),))


async def create_claim(user_id: int, channel_ids: list[str]) -> bool:
    """False when the user has taken the bonus already: it is given once."""
    row = await databaseExecutor.run(db.fetchone, """
        INSERT INTO channel_bonus_claims (user_id, channel_ids) VALUES (%s, %s)
        ON CONFLICT (user_id) DO NOTHING
        RETURNING user_id
    """, (int(user_id), channel_ids))
    return row is not None


async def set_lost(user_id: int, lost: bool) -> None:
    await databaseExecutor.run(db.fetchone, """
        UPDATE channel_bonus_claims
        SET lost_at = CASE WHEN %s THEN COALESCE(lost_at, LOCALTIMESTAMP) ELSE NULL END,
            checked_at = LOCALTIMESTAMP
        WHERE user_id = %s
        RETURNING user_id
    """, (lost, int(user_id)))


async def claims_to_check(limit: int) -> list[dict]:
    """Those not checked for a day, with what the bot needs to write to them."""
    return await databaseExecutor.run(db.fetchall, """
        SELECT c.*, u.service_id, u.language_code
        FROM channel_bonus_claims AS c
        INNER JOIN users AS u ON (u.id = c.user_id)
        WHERE c.checked_at < LOCALTIMESTAMP - interval '1 day'
        ORDER BY c.checked_at
        LIMIT %s
    """, (limit,)) or []


async def free_group_withheld(user_id: int) -> bool:
    """On the free tariff and no longer subscribed after taking the bonus: the free group waits."""
    row = await databaseExecutor.run(db.fetchone, """
        SELECT 1 AS withheld
        FROM channel_bonus_claims AS c
        INNER JOIN user_tariff_connections AS utc ON (utc.user_id = c.user_id)
        WHERE c.user_id = %s AND c.lost_at IS NOT NULL AND utc.tariff_id = 0
    """, (int(user_id),))
    return row is not None


async def claim_of(user_service_id: int | str) -> dict | None:
    """The claim by the user's Telegram id, with what the bot needs to write to them."""
    return await databaseExecutor.run(db.fetchone, """
        SELECT c.*, u.service_id, u.language_code
        FROM channel_bonus_claims AS c
        INNER JOIN users AS u ON (u.id = c.user_id)
        WHERE u.service_id = %s
    """, (str(user_service_id),))


async def mark_penalized(user_id: int, channel_service_id: str) -> int | None:
    """How many channels the user has lost days for, this one counted; None when it was counted already. One
    UPDATE, so the event and the daily check together cannot take the days twice."""
    row = await databaseExecutor.run(db.fetchone, """
        UPDATE channel_bonus_claims
        SET penalized_channel_ids = array_append(penalized_channel_ids, %s)
        WHERE user_id = %s AND NOT (%s = ANY(penalized_channel_ids))
        RETURNING cardinality(penalized_channel_ids) AS penalized
    """, (channel_service_id, int(user_id), channel_service_id))
    return row['penalized'] if row is not None else None
