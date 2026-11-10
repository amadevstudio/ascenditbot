"""The numbers of the bot: the whole bot for its owner (/admin), a group owner's groups (/usersCount)."""
from framework.repository.database_executor import databaseExecutor
from pkg.repository.database_connection import Database

db = Database()


async def collect() -> dict:
    users = await databaseExecutor.run(db.fetchone, """
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE u.language_code LIKE 'ru%%') AS ru,
            COUNT(*) FILTER (WHERE u.language_code LIKE 'en%%') AS en,
            COUNT(*) FILTER (WHERE u.created_at > LOCALTIMESTAMP - interval '1 day') AS day,
            COUNT(*) FILTER (WHERE u.created_at > LOCALTIMESTAMP - interval '7 days') AS week,
            COUNT(*) FILTER (WHERE u.created_at > LOCALTIMESTAMP - interval '30 days') AS month,
            COUNT(*) FILTER (WHERE EXISTS (
                SELECT 1 FROM user_moderated_chat_connections AS umcc WHERE umcc.user_id = u.id)) AS with_groups
        FROM users AS u
    """)
    # Who is on each tariff now and how they got there: paid once at least, the bonus for subscribing to the
    # channels (taken, never paid), the trial (neither)
    tariffs = await databaseExecutor.run(db.fetchall, """
        WITH people AS (
            SELECT COALESCE(utc.tariff_id, 0) AS tariff_id,
                EXISTS (SELECT 1 FROM payments_history AS ph WHERE ph.user_id = u.id AND ph.amount > 0) AS paid,
                EXISTS (SELECT 1 FROM channel_bonus_claims AS cbc WHERE cbc.user_id = u.id) AS bonus
            FROM users AS u
            LEFT JOIN user_tariff_connections AS utc ON utc.user_id = u.id
        )
        SELECT t.id, t.channels_count, COUNT(p.tariff_id) AS total,
            COUNT(p.tariff_id) FILTER (WHERE p.paid) AS paid,
            COUNT(p.tariff_id) FILTER (WHERE NOT p.paid AND p.bonus) AS bonus,
            COUNT(p.tariff_id) FILTER (WHERE NOT p.paid AND NOT p.bonus) AS trial
        FROM tariffs AS t
        LEFT JOIN people AS p ON p.tariff_id = t.id
        GROUP BY t.id, t.channels_count
        ORDER BY t.id
    """)
    bonus = await databaseExecutor.run(db.fetchone, """
        SELECT COUNT(*) AS taken, COUNT(*) FILTER (WHERE lost_at IS NOT NULL) AS lost FROM channel_bonus_claims
    """)
    groups = await databaseExecutor.run(db.fetchone, """
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE mc.active AND NOT mc.disabled) AS on,
            COUNT(*) FILTER (WHERE NOT mc.active AND NOT mc.disabled) AS paused,
            COUNT(*) FILTER (WHERE mc.disabled) AS disabled,
            COUNT(*) FILTER (WHERE mc.everyone_can_write) AS everyone,
            COUNT(*) FILTER (WHERE mc.post_limit IS NOT NULL) AS limited,
            (SELECT COUNT(*) FROM allowed_users) AS whitelisted,
            (SELECT COUNT(*) FROM allowed_users WHERE expires_at IS NOT NULL) AS timed,
            (SELECT COALESCE(SUM(deleted_messages_count), 0) FROM moderated_chat_statistics
                WHERE day = CURRENT_DATE) AS removed_day,
            (SELECT COALESCE(SUM(deleted_messages_count), 0) FROM moderated_chat_statistics
                WHERE day > CURRENT_DATE - 7) AS removed_week
        FROM moderated_chats AS mc
    """)
    month = await databaseExecutor.run(db.fetchall, """
        -- Refunds are negative rows: not counted as payments, taken off the sum
        SELECT ph.currency_code, COUNT(*) FILTER (WHERE ph.amount > 0) AS count, SUM(ph.amount) AS amount, c.minor_units
        FROM payments_history AS ph
        INNER JOIN users AS u ON u.id = ph.user_id AND u.is_admin IS FALSE
        LEFT JOIN currencies AS c ON c.code = ph.currency_code
        WHERE ph.created_at > LOCALTIMESTAMP - interval '30 days'
        GROUP BY ph.currency_code, c.minor_units
        ORDER BY ph.currency_code
    """)
    balances = await databaseExecutor.run(db.fetchall, """
        SELECT ub.currency_code, SUM(ub.balance) AS balance, c.minor_units
        FROM user_balances AS ub
        INNER JOIN users AS u ON u.id = ub.user_id AND u.is_admin IS FALSE
        LEFT JOIN currencies AS c ON c.code = ub.currency_code
        GROUP BY ub.currency_code, c.minor_units
        HAVING SUM(ub.balance) != 0
        ORDER BY ub.currency_code
    """)
    users = dict(users)
    users['other'] = users['total'] - users['ru'] - users['en']
    return {
        'users': users,
        'tariffs': [dict(row) for row in tariffs],
        'bonus': dict(bonus),
        'groups': dict(groups),
        'money': {
            'month': [{**dict(row), 'minor_units': row['minor_units'] if row['minor_units'] is not None else 2}
                      for row in month],
            'balances': [{**dict(row), 'minor_units': row['minor_units'] if row['minor_units'] is not None else 2}
                         for row in balances],
        },
    }


async def owner_groups(user_id: int) -> list[dict]:
    """The groups of one user (/usersCount for a group owner): state, whitelist and removed messages per group."""
    rows = await databaseExecutor.run(db.fetchall, """
        SELECT mc.id, mc.service_id, mc.name, mc.active, mc.disabled,
            (SELECT COUNT(*) FROM allowed_users AS au WHERE au.moderated_chat_id = mc.id AND au.active
                AND (au.expires_at IS NULL OR au.expires_at > LOCALTIMESTAMP)) AS whitelisted,
            (SELECT COUNT(*) FROM allowed_users AS au WHERE au.moderated_chat_id = mc.id AND au.active
                AND au.expires_at > LOCALTIMESTAMP) AS timed,
            (SELECT COALESCE(SUM(s.deleted_messages_count), 0) FROM moderated_chat_statistics AS s
                WHERE s.moderated_chat_id = mc.id AND s.day = CURRENT_DATE) AS removed_day,
            (SELECT COALESCE(SUM(s.deleted_messages_count), 0) FROM moderated_chat_statistics AS s
                WHERE s.moderated_chat_id = mc.id AND s.day > CURRENT_DATE - 7) AS removed_week,
            (SELECT COALESCE(SUM(s.deleted_messages_count), 0) FROM moderated_chat_statistics AS s
                WHERE s.moderated_chat_id = mc.id AND s.day > CURRENT_DATE - 30) AS removed_month
        FROM moderated_chats AS mc
        INNER JOIN user_moderated_chat_connections AS umcc ON umcc.moderated_chat_id = mc.id
        WHERE umcc.user_id = %s
        ORDER BY mc.id
    """, (user_id,))
    return [dict(row) for row in rows]
