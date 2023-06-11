import datetime
from typing import TypedDict, Generator, Literal, List

from framework.repository.database_executor import databaseExecutor
from pkg.repository import database_helpers
from pkg.repository.database_connection import Database, Connection
from project import constants
from project.constants import default_currency
from project.types import TariffInterface, UserTariffConnectionInterface, TariffInfoInterface, UserInterface, \
    PaymentHistoryInterface

db = Database()


class UserTariffInfoInterface(TypedDict, total=True):
    channels_count: int
    currency_code: str
    price: int
    balance: int
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


def _tariff_prices_for_user_selection() -> str:
    return """
        -- Take currency from user if connection not exists only
        (
            (tp.currency_code = utc.currency_code
                OR (tp.currency_code = lccc.currency_code AND utc.currency_code IS NULL)
                OR (tp.currency_code = 'usd' AND utc.currency_code IS NULL AND lccc.currency_code IS NULL)
            )
            OR tp.currency_code IS NULL
        )
    """


async def currency_code_for_user(user_id: int) -> str:
    result = await databaseExecutor.run(db.fetchone, f"""
        SELECT tp.currency_code
        FROM tariff_prices AS tp
        INNER JOIN users AS u ON (u.id = %s)
        LEFT JOIN user_tariff_connections AS utc ON (utc.user_id = u.id)
        LEFT JOIN lang_country_curr_codes AS lccc ON (lccc.language_code = u.language_code)
        WHERE {_tariff_prices_for_user_selection()}
        ORDER BY CASE WHEN tp.currency_code IS NOT NULL THEN 0 ELSE 1 END ASC
        LIMIT 1
    """, (user_id,))
    if result is None:
        return constants.default_currency

    return result['currency_code']


# Tariff info based on user currency
async def tariff_info(tariff_id: int, user_id: int) -> TariffInfoInterface | None:
    return await databaseExecutor.run(db.fetchone, f"""
        SELECT t.id, t.channels_count, tp.currency_code, tp.price
        FROM tariffs AS t
        LEFT JOIN users AS u ON (u.id = %s)
        LEFT JOIN user_tariff_connections AS utc ON (utc.user_id = u.id)
        LEFT JOIN lang_country_curr_codes AS lccc ON (lccc.language_code = u.language_code)
        INNER JOIN tariff_prices AS tp ON (
            t.id = tp.tariff_id
            AND {_tariff_prices_for_user_selection()}
        )
        WHERE t.id = %s
    """, (user_id, tariff_id,))


# User tariff and connection
async def user_tariff_info(user_id: int) -> UserTariffInfoInterface | None:
    return await databaseExecutor.run(db.fetchone, f"""
        SELECT t.channels_count,
            (CASE WHEN utc.currency_code IS NOT NULL THEN utc.currency_code ELSE lccc.currency_code END) 
                AS currency_code,
            tp.price,
            utc.balance, utc.end_date, utc.user_id, utc.tariff_id, utc.trial_was_activated
        FROM user_tariff_connections AS utc
        INNER JOIN tariffs AS t ON (t.id = utc.tariff_id)
        LEFT JOIN users AS u ON (u.id = utc.user_id)
        LEFT JOIN lang_country_curr_codes AS lccc ON (lccc.language_code = u.language_code)
        INNER JOIN tariff_prices AS tp ON (
            tp.tariff_id = t.id
            AND {_tariff_prices_for_user_selection()}
        )
        WHERE utc.user_id = %s
    """, (user_id,))


# Get all tariffs with user-based currencies
async def tariffs_info(user_id: int) -> list[TariffInfoInterface | None]:
    return await databaseExecutor.run(db.fetchall, f"""
        SELECT t.id, t.channels_count, tp.currency_code, tp.price
        FROM tariffs AS t
        LEFT JOIN users AS u ON (u.id = %s)
        LEFT JOIN user_tariff_connections AS utc ON (utc.user_id = u.id)
        LEFT JOIN lang_country_curr_codes AS lccc ON (lccc.language_code = u.language_code)
        INNER JOIN tariff_prices AS tp ON (
            t.id = tp.tariff_id
            AND {_tariff_prices_for_user_selection()}
        )
        ORDER BY t.id ASC
    """, (user_id,))


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
    else:
        result = await databaseExecutor.run(
            db.update_model, 'user_tariff_connections', subscription, key_fields=['user_id'])

    tariff = await databaseExecutor.run(db.find_model, 'tariffs', {'id': result['tariff_id']})

    if tariff is not None:
        await update_user_moderated_chats(subscription['user_id'], tariff['channels_count'])

    return result


async def get_currency_code_for_user(user_id: int) -> str:
    currency_code_row = await databaseExecutor.run(db.fetchone, """
            -- Take currency from user if connection not exists only
            SELECT (CASE WHEN utc.currency_code IS NOT NULL THEN utc.currency_code ELSE lccc.currency_code END)
                AS currency_code
            FROM user_tariff_connections AS utc
            LEFT JOIN users AS u ON (u.id = utc.user_id)
            LEFT JOIN lang_country_curr_codes AS lccc ON (lccc.language_code = u.language_code)
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


async def process_subscriptions() -> Generator[ProcessSubscriptionInterface, None, None]:
    users_set: List[ProlongableUserWithTariffIdInterface]
    tariffs = await tariffs_model_hash()

    prolongable_conditions = ["<", ">="]
    update_actions = [
        "SET tariff_id = 0, end_date = NULL",

        f"SET end_date = CURRENT_TIMESTAMP + interval '{constants.tariff_duration_days} day',"
        + "balance = balance - subscription_filter.tariff_price"
    ]

    for i in range(2):
        async for users_set in databaseExecutor.run_generator(db.update_many, """
            UPDATE user_tariff_connections AS utc
            {update_action}
            FROM users AS u
            INNER JOIN (
                SELECT utc.user_id, utc.balance >= tp.price * 2 AS prolongable, tp.price AS tariff_price
                FROM user_tariff_connections AS utc
                    INNER JOIN tariffs AS t ON (t.id = utc.tariff_id)
                    INNER JOIN tariff_prices AS tp ON (tp.tariff_id = t.id AND tp.currency_code = utc.currency_code)
                WHERE utc.tariff_id != 0
                    AND utc.balance {prolongable_condition} tp.price
                    AND utc.end_date < CURRENT_TIMESTAMP
            ) AS subscription_filter ON (u.id = subscription_filter.user_id)
            WHERE
                utc.user_id = subscription_filter.user_id
            RETURNING u.id, u.service_id, u.language_code, subscription_filter.prolongable, utc.tariff_id
        """.format(
            update_action=update_actions[i],
            prolongable_condition=prolongable_conditions[i]
        ), 100):
            print("\n\n!!!>!>>!>!")
            print(users_set, type(users_set))
            for user in users_set:
                await update_user_moderated_chats(user['id'], tariffs[user['tariff_id']]['channels_count'])

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

    connection: Connection
    async with db.get_connection() as connection:
        async with connection.transaction():
            # Disable after offset
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
            INNER JOIN tariff_prices AS tp ON (tp.tariff_id = t.id AND tp.currency_code = utc.currency_code)
        WHERE utc.tariff_id != 0
            AND utc.balance < tp.price
            AND utc.end_date > CURRENT_TIMESTAMP + interval '%s day' - interval '1 hour'
            AND utc.end_date < CURRENT_TIMESTAMP + interval '%s day'
    """, 100, (days_left, days_left,)):
        for user in users_set:
            yield user


async def increase_amount(user_id: int, amount: int) -> int:
    return (await databaseExecutor.run(db.execute_single_model, """
        UPDATE user_tariff_connections
        SET balance = balance + %s
        WHERE user_id = %s
    """, (amount, user_id,), returning='balance'))['balance']


async def move_end_date(user_id: int, days: int) -> datetime:
    return (await databaseExecutor.run(db.execute_single_model, """
        UPDATE user_tariff_connections
        SET end_date = end_date + interval '%s day'
        WHERE user_id = %s
    """, (days, user_id,), returning='end_date'))['end_date']


async def add_payment_history(payment_history_data: PaymentHistoryInterface) -> PaymentHistoryInterface:
    return await databaseExecutor.run(db.insert_model, 'payments_history', payment_history_data)
