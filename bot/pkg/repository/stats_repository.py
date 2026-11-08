"""The numbers of the bot (/usersCount): for its owner, users, groups, removed messages, money; for a group owner,
their groups."""
import json

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
                SELECT 1 FROM user_moderated_chat_connections AS umcc WHERE umcc.user_id = u.id)) AS with_groups,
            COUNT(*) FILTER (WHERE COALESCE(utc.tariff_id, 0) = 0) AS free,
            COUNT(*) FILTER (WHERE utc.tariff_id > 0) AS paid,
            COUNT(*) FILTER (WHERE utc.tariff_id > 0 AND NOT EXISTS (
                SELECT 1 FROM payments_history AS ph WHERE ph.user_id = u.id)) AS trial
        FROM users AS u
        LEFT JOIN user_tariff_connections AS utc ON utc.user_id = u.id
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


async def product_hunt_attribution() -> dict:
    """PH starts and current/mature 30-day owner funnels; only the bot owner sees this aggregate."""
    result = await databaseExecutor.run(db.fetchone, """
        WITH ph_users AS (
            SELECT id, created_at
            FROM users
            WHERE first_source = 'ph2' AND is_admin IS FALSE
                AND created_at >= CURRENT_TIMESTAMP - interval '12 months'
                AND created_at < CURRENT_TIMESTAMP
        ),
        windows AS (
            SELECT 'current'::text AS window_name
            UNION ALL SELECT 'mature'
        ),
        cohorts AS (
            SELECT 'current'::text AS window_name, id, created_at FROM ph_users
            UNION ALL
            SELECT 'mature'::text AS window_name, id, created_at FROM ph_users
            WHERE created_at <= CURRENT_TIMESTAMP - interval '30 days'
        ),
        window_counts AS (
            SELECT w.window_name, COUNT(c.id) AS registrations
            FROM windows w LEFT JOIN cohorts c ON c.window_name = w.window_name
            GROUP BY w.window_name
        ),
        cohort_events AS (
            SELECT c.window_name, c.id AS user_id, e.event_type, e.moderated_chat_id,
                e.owner, e.amount_minor, e.currency_code, cur.minor_units
            FROM cohorts c
            INNER JOIN attribution_events e ON e.user_id = c.id
            LEFT JOIN currencies cur ON cur.code = e.currency_code
            WHERE e.occurred_at >= c.created_at
                AND e.occurred_at < LEAST(c.created_at + interval '30 days', CURRENT_TIMESTAMP)
                AND e.event_type IN ('group_connected', 'owner_subscription_charged', 'owner_balance_refunded')
        ),
        funnel_metrics AS (
            SELECT window_name,
                COUNT(DISTINCT user_id) FILTER (
                    WHERE event_type = 'group_connected' AND owner IS TRUE) AS owners_connected,
                COUNT(DISTINCT moderated_chat_id) FILTER (
                    WHERE event_type = 'group_connected' AND owner IS TRUE) AS groups_connected,
                COUNT(DISTINCT user_id) FILTER (
                    WHERE event_type = 'owner_subscription_charged' AND amount_minor > 0) AS owners_paid
            FROM cohort_events
            GROUP BY window_name
        ),
        currency_totals AS (
            SELECT window_name, event_type, currency_code,
                SUM(amount_minor)::bigint AS amount, COUNT(*) AS count,
                COALESCE(minor_units, 2) AS minor_units
            FROM cohort_events
            WHERE event_type IN ('owner_subscription_charged', 'owner_balance_refunded')
                AND amount_minor > 0
            GROUP BY window_name, event_type, currency_code, minor_units
        ),
        currency_reports AS (
            SELECT window_name,
                COALESCE(jsonb_agg(jsonb_build_object(
                    'currency_code', currency_code, 'amount', amount, 'count', count, 'minor_units', minor_units
                )) FILTER (WHERE event_type = 'owner_subscription_charged'), '[]'::jsonb) AS paid_by_currency,
                COALESCE(jsonb_agg(jsonb_build_object(
                    'currency_code', currency_code, 'amount', amount, 'count', count, 'minor_units', minor_units
                )) FILTER (WHERE event_type = 'owner_balance_refunded'), '[]'::jsonb) AS refunds_by_currency
            FROM currency_totals
            GROUP BY window_name
        ),
        window_reports AS (
            SELECT w.window_name, wc.registrations,
                COALESCE(fm.owners_connected, 0) AS owners_connected,
                COALESCE(fm.groups_connected, 0) AS groups_connected,
                COALESCE(fm.owners_paid, 0) AS owners_paid,
                COALESCE(cr.paid_by_currency, '[]'::jsonb) AS paid_by_currency,
                COALESCE(cr.refunds_by_currency, '[]'::jsonb) AS refunds_by_currency
            FROM windows w
            INNER JOIN window_counts wc USING (window_name)
            LEFT JOIN funnel_metrics fm USING (window_name)
            LEFT JOIN currency_reports cr USING (window_name)
        )
        SELECT
            (SELECT COUNT(*) FROM attribution_events e
                WHERE e.event_type = 'bot_start' AND e.touch_source = 'ph2'
                    AND e.occurred_at >= CURRENT_TIMESTAMP - interval '12 months'
                    AND e.occurred_at < CURRENT_TIMESTAMP) AS starts,
            (SELECT COUNT(DISTINCT e.user_id) FROM attribution_events e
                WHERE e.event_type = 'bot_start' AND e.touch_source = 'ph2'
                    AND e.is_new_user IS TRUE
                    AND e.occurred_at >= CURRENT_TIMESTAMP - interval '12 months'
                    AND e.occurred_at < CURRENT_TIMESTAMP) AS new_starters,
            (SELECT COUNT(DISTINCT e.user_id) FROM attribution_events e
                WHERE e.event_type = 'bot_start' AND e.touch_source = 'ph2'
                    AND e.is_new_user IS FALSE
                    AND e.occurred_at >= CURRENT_TIMESTAMP - interval '12 months'
                    AND e.occurred_at < CURRENT_TIMESTAMP) AS returning_starters,
            (SELECT COUNT(*) FROM ph_users) AS registrations,
            (SELECT jsonb_agg(jsonb_build_object(
                'window', window_name, 'registrations', registrations,
                'owners_connected', owners_connected, 'groups_connected', groups_connected,
                'owners_paid', owners_paid, 'paid_by_currency', paid_by_currency,
                'refunds_by_currency', refunds_by_currency
            )) FROM window_reports) AS windows
    """)
    report = dict(result)
    windows = report.pop('windows')
    if isinstance(windows, str):
        windows = json.loads(windows)
    report.update({row['window']: row for row in windows})
    return report


async def delete_expired_attribution_events() -> int:
    """Enforce the documented 12-month detail retention from the existing hourly task."""
    result = await databaseExecutor.run(db.fetchone, """
        WITH deleted AS (
            DELETE FROM attribution_events
            WHERE occurred_at < CURRENT_TIMESTAMP - interval '12 months'
            RETURNING 1
        ) SELECT COUNT(*) AS count FROM deleted
    """)
    return result['count']
