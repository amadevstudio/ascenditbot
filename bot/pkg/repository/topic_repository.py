"""The topics of groups with topics, as the bot has seen them (migrator 20261115120000_chat_topics)."""
from framework.repository.database_executor import databaseExecutor
from pkg.repository.database_connection import Database

db = Database()


async def seen(chat_id: int, thread_id: int, name: str | None, closed: bool | None) -> dict:
    """Remembers a topic a message came from and says whether it is protected, and whether the group has a topic
    the bot leaves alone (or will: new topics free). A new topic is protected as the group's setting for new topics says. `name` and `closed`
    are kept as they were when None (a message that does not tell them)."""
    return await databaseExecutor.run(db.fetchone, """
        WITH topic AS (
            INSERT INTO chat_topics (moderated_chat_id, thread_id, name, closed, protected)
            VALUES ($1, $2, $3, COALESCE($4::boolean, false),
                    (SELECT topics_default_protected FROM moderated_chats WHERE id = $1))
            ON CONFLICT (moderated_chat_id, thread_id) DO UPDATE SET
                name = COALESCE(EXCLUDED.name, chat_topics.name),
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
    """, (int(chat_id), int(thread_id), name, closed))


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
