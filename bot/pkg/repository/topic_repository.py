"""The topics of groups with topics, as the bot has seen them or found them through MTProto (migrators
20261116120000_chat_topics, 20261117120000_chat_topics_scan)."""
from framework.repository.database_executor import databaseExecutor
from pkg.repository.database_connection import Database

db = Database()


async def seen(chat_id: int, thread_id: int, name: str | None, name_hint: str | None, closed: bool | None) -> dict:
    """Remembers a topic a message came from and says whether it is protected, and whether the group has a topic
    the bot leaves alone (or will: new topics free). A new topic is protected as the group's setting for new topics
    says. `name` (from "created" or "renamed") replaces the kept one; `name_hint` (the topic's first message, with
    the name it was created with) only fills a missing one. `closed` is kept as it was when None."""
    return await databaseExecutor.run(db.fetchone, """
        WITH topic AS (
            INSERT INTO chat_topics (moderated_chat_id, thread_id, name, closed, protected)
            VALUES ($1, $2, COALESCE($3, $5), COALESCE($4::boolean, false),
                    (SELECT topics_default_protected FROM moderated_chats WHERE id = $1))
            ON CONFLICT (moderated_chat_id, thread_id) DO UPDATE SET
                name = COALESCE($3, chat_topics.name, $5),
                closed = COALESCE($4::boolean, chat_topics.closed),
                seen_at = LOCALTIMESTAMP
            RETURNING protected, name
        )
        SELECT topic.protected, topic.name,
            NOT topic.protected
            OR NOT (SELECT topics_default_protected FROM moderated_chats WHERE id = $1)
            OR EXISTS (
                SELECT 1 FROM chat_topics
                WHERE moderated_chat_id = $1 AND thread_id <> $2 AND NOT protected
            ) AS has_free
        FROM topic
    """, (int(chat_id), int(thread_id), name, closed, name_hint))


async def of_chat(chat_id: int, limit: int, offset: int) -> list[dict]:
    """The general topic first, then the open ones in the order they were made, the closed ones last."""
    return await databaseExecutor.run(db.fetchall, """
        SELECT * FROM chat_topics WHERE moderated_chat_id = %s
        ORDER BY closed, thread_id <> 1, thread_id
        LIMIT %s OFFSET %s
    """, (int(chat_id), limit, offset)) or []


async def counts(chat_id: int) -> dict:
    return await databaseExecutor.run(db.fetchone, """
        SELECT COUNT(*) AS total, COUNT(*) FILTER (WHERE protected) AS protected
        FROM chat_topics WHERE moderated_chat_id = %s
    """, (int(chat_id),))


async def toggle(chat_id: int, thread_id: int) -> dict | None:
    return await databaseExecutor.run(db.fetchone, """
        UPDATE chat_topics SET protected = NOT protected
        WHERE moderated_chat_id = %s AND thread_id = %s
        RETURNING *
    """, (int(chat_id), int(thread_id)))


async def set_default(chat_id: int, protected: bool) -> None:
    await databaseExecutor.run(db.fetchone, """
        UPDATE moderated_chats SET topics_default_protected = %s, updated_at = LOCALTIMESTAMP WHERE id = %s
        RETURNING id
    """, (protected, int(chat_id)))


async def protected(chat_id: int) -> list[dict]:
    rows = await databaseExecutor.run(db.fetchall, """
        SELECT thread_id, name FROM chat_topics WHERE moderated_chat_id = %s AND protected AND NOT closed
        ORDER BY thread_id <> 1, thread_id
    """, (int(chat_id),)) or []
    return list(rows)


async def thread_ids(chat_id: int) -> list[int]:
    rows = await databaseExecutor.run(db.fetchall, """
        SELECT thread_id FROM chat_topics WHERE moderated_chat_id = %s ORDER BY thread_id
    """, (int(chat_id),)) or []
    return [row['thread_id'] for row in rows]


async def found(chat_id: int, thread_id: int, name: str | None, closed: bool) -> None:
    """A topic as Telegram says it is now: its name and state replace the kept ones; a new one is protected as the
    group's setting for new topics says."""
    await databaseExecutor.run(db.fetchone, """
        INSERT INTO chat_topics (moderated_chat_id, thread_id, name, closed, protected)
        VALUES ($1, $2, $3, $4, (SELECT topics_default_protected FROM moderated_chats WHERE id = $1))
        ON CONFLICT (moderated_chat_id, thread_id) DO UPDATE SET
            name = COALESCE(EXCLUDED.name, chat_topics.name), closed = EXCLUDED.closed
        RETURNING thread_id
    """, (int(chat_id), int(thread_id), name, closed))


async def delete(chat_id: int, thread_ids: list[int]) -> None:
    if not thread_ids:
        return
    await databaseExecutor.run(db.fetchall, """
        DELETE FROM chat_topics WHERE moderated_chat_id = $1 AND thread_id = ANY($2::bigint[]) RETURNING thread_id
    """, (int(chat_id), [int(thread_id) for thread_id in thread_ids]))


async def save_scan(chat_id: int, scanned_to: int, upper: int, finished: bool) -> None:
    await databaseExecutor.run(db.fetchone, """
        UPDATE moderated_chats SET topics_scanned_to = $2, topics_scan_upper = $3,
            topics_scanned_at = CASE WHEN $4 THEN LOCALTIMESTAMP ELSE topics_scanned_at END
        WHERE id = $1
        RETURNING id
    """, (int(chat_id), int(scanned_to), int(upper), finished))
