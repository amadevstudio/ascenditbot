import datetime
from typing import TypedDict, Generator, Literal, List

from framework.repository.database_executor import databaseExecutor
from pkg.repository import database_helpers
from pkg.repository.database_connection import Database
from project import constants
from project.constants import default_currency
from project.types import CurrencyInterface, TariffInterface, UserBalanceInterface, UserTariffConnectionInterface, \
    TariffInfoInterface, UserInterface, PaymentHistoryInterface

db = Database()


class UserTariffInfoInterface(TypedDict, total=True):
    channels_count: int
    currency_code: str
    price: int
    balance: int
    balances: list[UserBalanceInterface]
    end_date: datetime.datetime | None
    user_id: int
    tariff_id: int | None
    trial_was_activated: bool


class ProlongableUserWithTariffIdInterface(UserInterface):
    prolongable: bool
    tariff_id: int


class ProcessSubscriptionInterface(TypedDict):
    user: UserInterface
    action: Literal['prolonged', 'disabled']
    prolongable: bool


# async def find(tariff_id: int) -> TariffInterface | None:
#     return await databaseExecutor.run(db.find_model, 'tariffs', {'id': tariff_id})


def _tariff_prices_for_currency_selection(currency_code: str = 'payment_currency_code') -> str:
    return f"""
        tp.currency_code = {currency_code}
    """


async def enabled_currencies() -> list[CurrencyInterface]:
    return await databaseExecutor.run(db.fetchall, """
        SELECT *
        FROM currencies
        WHERE enabled IS TRUE
        ORDER BY code ASC
    """)


async def ensure_user_balances(user_id: int):
    await databaseExecutor.run(db.execute_single_model, """
        INSERT INTO user_balances (user_id, currency_code, balance, created_at, updated_at)
        SELECT %s, c.code, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
        FROM currencies AS c
        WHERE c.enabled IS TRUE
        ON CONFLICT (user_id, currency_code) DO NOTHING
    """, (user_id,))


async def user_balances(user_id: int) -> list[UserBalanceInterface]:
    await ensure_user_balances(user_id)
    return await databaseExecutor.run(db.fetchall, """
        SELECT ub.*
        FROM user_balances AS ub
        INNER JOIN currencies AS c ON (c.code = ub.currency_code)
        WHERE ub.user_id = %s AND c.enabled IS TRUE
        ORDER BY ub.currency_code ASC
    """, (user_id,))


async def currency_code_for_user(user_id: int) -> str:
    result = await databaseExecutor.run(db.fetchone, f"""
        SELECT
            CASE
                WHEN c.enabled IS TRUE THEN c.code
                ELSE %s
            END AS currency_code
        FROM users AS u
        LEFT JOIN user_tariff_connections AS utc ON (utc.user_id = u.id)
        LEFT JOIN lang_country_curr_codes AS lccc ON (lccc.language_code = u.language_code)
        LEFT JOIN currencies AS c ON (c.code = COALESCE(utc.payment_currency_code, lccc.currency_code, %s))
        WHERE u.id = %s
        LIMIT 1
    """, (constants.default_currency, constants.default_currency, user_id,))
    if result is None:
        return constants.default_currency

    return result['currency_code']


async def set_payment_currency(user_id: int, currency_code: str) -> UserTariffConnectionInterface | None:
    currency = await databaseExecutor.run(db.fetchone, """
        SELECT code FROM currencies WHERE code = %s AND enabled IS TRUE
    """, (currency_code,))
    if currency is None:
        return None

    await ensure_user_balances(user_id)
    return await databaseExecutor.run(db.update_model, 'user_tariff_connections', {
        'user_id': user_id,
        'payment_currency_code': currency_code
    }, key_fields=['user_id'])


# Tariff info based on user currency
async def tariff_info(tariff_id: int, user_id: int) -> TariffInfoInterface | None:
    currency_code = await currency_code_for_user(user_id)
    return await tariff_info_by_currency(tariff_id, currency_code)


async def tariff_info_by_currency(tariff_id: int, currency_code: str) -> TariffInfoInterface | None:
    return await databaseExecutor.run(db.fetchone, f"""
        SELECT t.id, t.channels_count, tp.currency_code, tp.price
        FROM tariffs AS t
        INNER JOIN tariff_prices AS tp ON (
            t.id = tp.tariff_id
            AND {_tariff_prices_for_currency_selection('%s')}
        )
        WHERE t.id = %s
    """, (currency_code, tariff_id,))


# User tariff and connection
async def user_tariff_info(user_id: int) -> UserTariffInfoInterface | None:
    await ensure_user_balances(user_id)
    tariff_info_row = await databaseExecutor.run(db.fetchone, f"""
        SELECT t.channels_count,
            utc.payment_currency_code AS currency_code,
            tp.price,
            COALESCE(ub.balance, 0) AS balance,
            utc.end_date, utc.user_id, utc.tariff_id, utc.trial_was_activated
        FROM user_tariff_connections AS utc
        INNER JOIN tariffs AS t ON (t.id = utc.tariff_id)
        LEFT JOIN user_balances AS ub ON (
            ub.user_id = utc.user_id AND ub.currency_code = utc.payment_currency_code
        )
        INNER JOIN tariff_prices AS tp ON (
            tp.tariff_id = t.id
            AND {_tariff_prices_for_currency_selection('utc.payment_currency_code')}
        )
        WHERE utc.user_id = %s
    """, (user_id,))
    if tariff_info_row is None:
        return None

    return {
        **dict(tariff_info_row),
        'balances': await user_balances(user_id)
    }


# Get all tariffs with user-based currencies
async def tariffs_info(user_id: int) -> list[TariffInfoInterface | None]:
    currency_code = await currency_code_for_user(user_id)
    return await tariffs_info_by_currency(currency_code)


async def tariffs_info_by_currency(currency_code: str) -> list[TariffInfoInterface | None]:
    return await databaseExecutor.run(db.fetchall, f"""
        SELECT t.id, t.channels_count, tp.currency_code, tp.price
        FROM tariffs AS t
        INNER JOIN tariff_prices AS tp ON (
            t.id = tp.tariff_id
            AND {_tariff_prices_for_currency_selection('%s')}
        )
        ORDER BY t.id ASC
    """, (currency_code,))


async def tariffs_model_hash() -> dict[int, TariffInfoInterface]:
    return database_helpers.hashed_by_id(await databaseExecutor.run(db.fetchall, f"""
        SELECT t.*
        FROM tariffs AS t
        ORDER BY t.id ASC
    """))


async def user_subscription(user_id: int) -> UserTariffConnectionInterface | None:
    return await databaseExecutor.run(db.find_model, 'user_tariff_connections', {'user_id': user_id})


async def update_subscription(subscription: UserTariffConnectionInterface, create: bool = False) \
        -> UserTariffConnectionInterface:
    if create:
        result = await databaseExecutor.run(db.insert_model, 'user_tariff_connections', subscription)
        await ensure_user_balances(subscription['user_id'])
    else:
        result = await databaseExecutor.run(
            db.update_model, 'user_tariff_connections', subscription, key_fields=['user_id'])

    tariff = await databaseExecutor.run(db.find_model, 'tariffs', {'id': result['tariff_id']})

    if tariff is not None:
        await update_user_moderated_chats(subscription['user_id'], tariff['channels_count'])

    return result


async def update_subscription_with_balance_delta(
        subscription: UserTariffConnectionInterface, balance_delta: int, currency_code: str
) -> UserTariffConnectionInterface:
    async with db.get_connection() as connection:
        async with connection.transaction():
            if balance_delta != 0:
                await databaseExecutor.run(db.execute_single_model, """
                    UPDATE user_balances
                    SET balance = balance + %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = %s AND currency_code = %s
                """, (balance_delta, subscription['user_id'], currency_code,), connection=connection)

            result = await databaseExecutor.run(
                db.update_model, 'user_tariff_connections', subscription, key_fields=['user_id'],
                connection=connection)

    tariff = await databaseExecutor.run(db.find_model, 'tariffs', {'id': result['tariff_id']})
    if tariff is not None:
        await update_user_moderated_chats(subscription['user_id'], tariff['channels_count'])

    return result


async def get_currency_code_for_user(user_id: int) -> str:
    currency_code_row = await databaseExecutor.run(db.fetchone, """
            SELECT utc.payment_currency_code AS currency_code
            FROM user_tariff_connections AS utc
            WHERE utc.user_id = %s
        """, (user_id,))
    if currency_code_row is None:
        return default_currency

    return currency_code_row.get('currency_code', default_currency)


# If the user has fewer chats than in his subscription (5 < 6 -> true, 6 < 6 -> false)
async def chats_number_satisfactory(chat_id: str, strong: bool = True) -> bool:
    return (await databaseExecutor.run(db.fetchone, f"""
        SELECT
            CASE WHEN t.channels_count IS NULL
            THEN TRUE
            ELSE (
                    CASE WHEN user_chats_stat.chats_count IS NULL THEN 0 ELSE user_chats_stat.chats_count END
                ) {('<' if strong else '<=')} t.channels_count
            END AS satisfies

            -- , CASE WHEN user_chats_stat.chats_count IS NULL THEN 0 ELSE user_chats_stat.chats_count END
            -- , t.channels_count

            FROM users AS u
        LEFT JOIN (
            SELECT COUNT(*) AS chats_count, umcc.user_id AS user_id
            FROM user_moderated_chat_connections AS umcc
            WHERE umcc.owner IS TRUE
            GROUP BY umcc.user_id
        ) AS user_chats_stat ON (user_chats_stat.user_id = u.id)
        INNER JOIN user_tariff_connections AS utc ON (utc.user_id = u.id)
        INNER JOIN tariffs AS t ON (t.id = utc.tariff_id)
        WHERE u.service_id = %s
    """, (chat_id,)))['satisfies']


async def process_subscriptions(update_batch: int = 1000) -> Generator[ProcessSubscriptionInterface, None, None]:
    users_set: List[ProlongableUserWithTariffIdInterface | None]
    tariffs = await tariffs_model_hash()

    queries = [
        """
            UPDATE user_tariff_connections AS utc
            SET tariff_id = 0, end_date = NULL
            FROM users AS u
            INNER JOIN (
                SELECT utc.user_id, ub.balance >= tp.price * 2 AS prolongable
                FROM user_tariff_connections AS utc
                    INNER JOIN tariffs AS t ON (t.id = utc.tariff_id)
                    INNER JOIN tariff_prices AS tp ON (
                        tp.tariff_id = t.id AND tp.currency_code = utc.payment_currency_code)
                    INNER JOIN user_balances AS ub ON (
                        ub.user_id = utc.user_id AND ub.currency_code = utc.payment_currency_code)
                WHERE utc.tariff_id != 0
                    AND ub.balance < tp.price
                    AND utc.end_date < CURRENT_TIMESTAMP
                LIMIT {update_batch}
            ) AS subscription_filter ON (u.id = subscription_filter.user_id)
            WHERE utc.user_id = u.id
            RETURNING u.id, u.service_id, u.language_code, subscription_filter.prolongable, utc.tariff_id
        """,
        """
            WITH subscription_filter AS (
                SELECT utc.user_id, ub.balance >= tp.price * 2 AS prolongable, tp.price AS tariff_price
                FROM user_tariff_connections AS utc
                    INNER JOIN tariffs AS t ON (t.id = utc.tariff_id)
                    INNER JOIN tariff_prices AS tp ON (
                        tp.tariff_id = t.id AND tp.currency_code = utc.payment_currency_code)
                    INNER JOIN user_balances AS ub ON (
                        ub.user_id = utc.user_id AND ub.currency_code = utc.payment_currency_code)
                WHERE utc.tariff_id != 0
                    AND ub.balance >= tp.price
                    AND utc.end_date < CURRENT_TIMESTAMP
                LIMIT {update_batch}
            ),
            updated_balance AS (
                UPDATE user_balances AS ub
                SET balance = ub.balance - subscription_filter.tariff_price,
                    updated_at = CURRENT_TIMESTAMP
                FROM subscription_filter
                INNER JOIN user_tariff_connections AS utc ON (utc.user_id = subscription_filter.user_id)
                WHERE ub.user_id = subscription_filter.user_id
                    AND ub.currency_code = utc.payment_currency_code
                RETURNING ub.user_id
            )
            UPDATE user_tariff_connections AS utc
            SET end_date = CURRENT_TIMESTAMP + interval '{tariff_duration_days} day'
            FROM users AS u
            INNER JOIN subscription_filter ON (u.id = subscription_filter.user_id)
            INNER JOIN updated_balance ON (updated_balance.user_id = subscription_filter.user_id)
            WHERE utc.user_id = u.id
            RETURNING u.id, u.service_id, u.language_code, subscription_filter.prolongable, utc.tariff_id
        """
    ]

    for i in range(2):
        users_set = [None]
        while len(users_set) > 0:
            users_set = await databaseExecutor.run(db.update_many, queries[i].format(
                update_batch=update_batch,
                tariff_duration_days=constants.tariff_duration_days
            ), 100)
            for user in users_set:
                await update_user_moderated_chats(
                    user['id'], tariffs[user['tariff_id']]['channels_count'])

                yield {
                    'user': {
                        'id': user['id'],
                        'service_id': user['service_id'],
                        'language_code': user['language_code']
                    },
                    'action': 'disabled' if i == 0 else 'prolonged',
                    'prolongable': user['prolongable']
                }


async def update_user_moderated_chats(user_id: int, offset: int | None):
    # All enabled
    if offset is None:
        await databaseExecutor.run(db.execute_single_model, """
            UPDATE moderated_chats AS mc
            SET disabled = FALSE
            FROM user_moderated_chat_connections AS umcc
            WHERE
                umcc.moderated_chat_id = mc.id
                AND umcc.user_id = %s
                AND umcc.owner IS TRUE
        """, (user_id,))
        return

    # Some or all disabled
    async with db.get_connection() as connection:
        async with connection.transaction():
            await databaseExecutor.run(db.execute_single_model, """
                UPDATE moderated_chats AS mc
                SET disabled = TRUE
                WHERE mc.id IN (
                    SELECT ummc.moderated_chat_id
                    FROM user_moderated_chat_connections AS ummc
                    WHERE
                        ummc.user_id = %s
                        AND ummc.owner = TRUE
                    ORDER BY id ASC
                    OFFSET %s
                )
            """, (user_id, offset,), connection=connection)

            # Enable before offset
            await databaseExecutor.run(db.execute_single_model, """
                UPDATE moderated_chats AS mc
                SET disabled = FALSE
                WHERE mc.id IN (
                    SELECT ummc.moderated_chat_id
                    FROM user_moderated_chat_connections AS ummc
                    WHERE
                        ummc.user_id = %s
                        AND ummc.owner = TRUE
                    ORDER BY id ASC
                    LIMIT %s
                )
            """, (user_id, offset,), connection=connection)


async def users_with_remaining_days(days_left: int) -> Generator[UserInterface, None, None]:
    async for users_set in databaseExecutor.run_generator(db.fetchmany, """
        SELECT u.*
        FROM users AS u
            INNER JOIN user_tariff_connections AS utc ON (utc.user_id = u.id)
            INNER JOIN tariffs AS t ON (t.id = utc.tariff_id)
            INNER JOIN tariff_prices AS tp ON (
                tp.tariff_id = t.id AND tp.currency_code = utc.payment_currency_code)
            INNER JOIN user_balances AS ub ON (
                ub.user_id = utc.user_id AND ub.currency_code = utc.payment_currency_code)
        WHERE utc.tariff_id != 0
            AND ub.balance < tp.price
            AND utc.end_date > CURRENT_TIMESTAMP + interval '{days_left} day' - interval '1 hour'
            AND utc.end_date < CURRENT_TIMESTAMP + interval '{days_left} day'
    """.format(days_left=days_left), 100):
        for user in users_set:
            yield user


async def increase_amount(user_id: int, amount: int, currency_code: str) -> int:
    await ensure_user_balances(user_id)
    return (await databaseExecutor.run(db.execute_single_model, """
        UPDATE user_balances
        SET balance = balance + %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE user_id = %s AND currency_code = %s
    """, (amount, user_id, currency_code,), returning='balance'))['balance']


async def move_end_date(user_id: int, days: int) -> datetime:
    return (await databaseExecutor.run(db.execute_single_model, """
        UPDATE user_tariff_connections
        SET end_date = end_date + interval '%s day'
        WHERE user_id = %s
    """, (days, user_id,), returning='end_date'))['end_date']


async def add_payment_history(payment_history_data: PaymentHistoryInterface) -> PaymentHistoryInterface:
    return await databaseExecutor.run(db.insert_model, 'payments_history', payment_history_data)
