"""The links t.me/<bot>?start=src_<tag> (migrator 20261115120000_attribution_sources) and what the people they
brought did (attribution_events, 20261114120000_product_hunt_attribution): the reports of the admin pages, Sources."""
import json

from framework.repository.database_executor import databaseExecutor
from pkg.repository.database_connection import Database

db = Database()

# The cohort of the users who came without a known link (users.first_source)
UNTAGGED = 'direct_unknown'


async def sources() -> list[dict]:
    """The owner's tags, the oldest first, with the starts by each link and the new users it brought in 12 months."""
    return await databaseExecutor.run(db.fetchall, """
        SELECT s.tag,
            (SELECT COUNT(*) FROM attribution_events AS e
                WHERE e.event_type = 'bot_start' AND e.touch_source = s.tag
                    AND e.occurred_at >= CURRENT_TIMESTAMP - interval '12 months') AS starts,
            (SELECT COUNT(*) FROM users AS u
                WHERE u.first_source = s.tag AND u.is_admin IS FALSE
                    AND u.created_at >= CURRENT_TIMESTAMP - interval '12 months') AS registrations
        FROM attribution_sources AS s
        ORDER BY s.created_at, s.tag
    """, ()) or []


async def untagged_registrations() -> int:
    return (await databaseExecutor.run(db.fetchone, """
        SELECT COUNT(*) FROM users
        WHERE first_source = %s AND is_admin IS FALSE AND created_at >= CURRENT_TIMESTAMP - interval '12 months'
    """, (UNTAGGED,)))['count']


async def is_source(tag: str) -> bool:
    return await databaseExecutor.run(db.fetchone, """
        SELECT tag FROM attribution_sources WHERE tag = %s
    """, (tag,)) is not None


async def add_source(tag: str) -> None:
    await databaseExecutor.run(db.fetchone, """
        INSERT INTO attribution_sources (tag) VALUES (%s) ON CONFLICT (tag) DO NOTHING RETURNING tag
    """, (tag,))


async def delete_source(tag: str) -> bool:
    """New starts by the link stop counting; the users it brought keep it as their first source."""
    return await databaseExecutor.run(db.fetchone, """
        DELETE FROM attribution_sources WHERE tag = %s RETURNING tag
    """, (tag,)) is not None


async def funnel(tag: str) -> dict:
    """The starts by the tag's link and the current/mature 30-day owner funnels of those it brought."""
    result = await databaseExecutor.run(db.fetchone, """
        WITH cohort_users AS (
            SELECT id, created_at
            FROM users
            WHERE first_source = %s AND is_admin IS FALSE
                AND created_at >= CURRENT_TIMESTAMP - interval '12 months'
                AND created_at < CURRENT_TIMESTAMP
        ),
        windows AS (
            SELECT 'current'::text AS window_name
            UNION ALL SELECT 'mature'
        ),
        cohorts AS (
            SELECT 'current'::text AS window_name, id, created_at FROM cohort_users
            UNION ALL
            SELECT 'mature'::text AS window_name, id, created_at FROM cohort_users
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
                WHERE e.event_type = 'bot_start' AND e.touch_source = %s
                    AND e.occurred_at >= CURRENT_TIMESTAMP - interval '12 months'
                    AND e.occurred_at < CURRENT_TIMESTAMP) AS starts,
            (SELECT COUNT(DISTINCT e.user_id) FROM attribution_events e
                WHERE e.event_type = 'bot_start' AND e.touch_source = %s
                    AND e.is_new_user IS TRUE
                    AND e.occurred_at >= CURRENT_TIMESTAMP - interval '12 months'
                    AND e.occurred_at < CURRENT_TIMESTAMP) AS new_starters,
            (SELECT COUNT(DISTINCT e.user_id) FROM attribution_events e
                WHERE e.event_type = 'bot_start' AND e.touch_source = %s
                    AND e.is_new_user IS FALSE
                    AND e.occurred_at >= CURRENT_TIMESTAMP - interval '12 months'
                    AND e.occurred_at < CURRENT_TIMESTAMP) AS returning_starters,
            (SELECT COUNT(*) FROM cohort_users) AS registrations,
            (SELECT jsonb_agg(jsonb_build_object(
                'window', window_name, 'registrations', registrations,
                'owners_connected', owners_connected, 'groups_connected', groups_connected,
                'owners_paid', owners_paid, 'paid_by_currency', paid_by_currency,
                'refunds_by_currency', refunds_by_currency
            )) FROM window_reports) AS windows
    """, (tag,) * 4)
    report = dict(result)
    windows = report.pop('windows')
    if isinstance(windows, str):
        windows = json.loads(windows)
    report.update({row['window']: row for row in windows})
    return report


async def delete_expired_events() -> int:
    """Enforce the documented 12-month detail retention from the existing hourly task."""
    result = await databaseExecutor.run(db.fetchone, """
        WITH deleted AS (
            DELETE FROM attribution_events
            WHERE occurred_at < CURRENT_TIMESTAMP - interval '12 months'
            RETURNING 1
        ) SELECT COUNT(*) AS count FROM deleted
    """)
    return result['count']
