import datetime
from typing import TypedDict, Generator, Literal, List

from pkg.repository import database_helpers
from pkg.repository.database_connection import Database
from project import constants
from project.constants import default_currency
from project.types import TariffInterface, UserTariffConnectionInterface, TariffInfoInterface, UserInterface

db = Database()


class UserTariffInfoInterface(TypedDict, total=True):
    channels_count: int
    currency_code: str
    price: int
    balance: int
    start_date: datetime.datetime | None
    user_id: int
    tariff_id: int | None


class ProlongableUserWithTariffIdInterface(UserInterface):
    prolongable: bool
    tariff_id: int


class ProcessSubscriptionInterface(TypedDict):
    user: UserInterface
    action: Literal['prolonged', 'disabled']
    prolongable: bool


def find(tariff_id: int) -> TariffInterface | None:
    return db.find_model('tariffs', {'id': tariff_id})


def _tariff_prices_for_user_selection() -> str:
    return """
        -- Take currency from user if connection not exists only
        (
            (tp.currency_code = utc.currency_code
                -- OR (tp.currency_code = lccc.currency_code AND utc.currency_code IS NULL)
                -- OR (tp.currency_code = 'usd' AND utc.currency_code IS NULL AND lccc.currency_code IS NULL)
            )
            OR tp.currency_code IS NULL
        )
    """


def currency_code_for_user(user_id: int) -> str:
    result = db.fetchone(f"""
        SELECT tp.currency_code
        FROM tariff_prices AS tp
        INNER JOIN users AS u ON (u.id = 3)
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
def tariff_info(tariff_id: int, user_id: int) -> TariffInfoInterface | None:
    return db.fetchone(f"""
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
def user_tariff_info(user_id: int) -> UserTariffInfoInterface | None:
    return db.fetchone(f"""
        SELECT t.channels_count,
            (CASE WHEN utc.currency_code IS NOT NULL THEN utc.currency_code ELSE lccc.currency_code END) 
                AS currency_code,
            tp.price,
            utc.balance, utc.start_date, utc.user_id, utc.tariff_id
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


def tariffs_info(user_id: int) -> list[TariffInfoInterface | None]:
    return db.fetchall(f"""
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


def tariffs_model_hash() -> dict[int, TariffInfoInterface]:
    return database_helpers.hashed_by_id(db.fetchall(f"""
        SELECT t.*
        FROM tariffs AS t
        ORDER BY t.id ASC
    """))


def update_subscription(subscription: UserTariffConnectionInterface) -> UserTariffConnectionInterface:
    result = db.insert_model(
        'user_tariff_connections', subscription,
        conflict_unique_fields=['user_id'])

    tariff = db.find_model('tariffs', {'id': result['tariff_id']})

    if tariff is not None:
        update_user_moderated_chats(subscription['user_id'], tariff['channels_count'])

    return result


def get_currency_code_for_user(user_id: int) -> str:
    currency_code_row = db.fetchone("""
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


def chats_number_satisfactory(chat_id: str) -> bool:
    return db.fetchone("""
        SELECT
            CASE WHEN t.channels_count IS NULL
            THEN TRUE
            ELSE (
                    CASE WHEN user_chats_stat.chats_count IS NULL THEN 0 ELSE user_chats_stat.chats_count END
                ) < t.channels_count
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
    """, (chat_id,))['satisfies']


def process_subscriptions() -> Generator[ProcessSubscriptionInterface, None, None]:
    users_set: List[ProlongableUserWithTariffIdInterface]
    tariffs = tariffs_model_hash()

    prolongable_conditions = ["<", ">="]
    update_actions = [
        "SET tariff_id = 0, start_date = NULL",
        "SET start_date = NOW(), balance = balance - subscription_filter.tariff_price"
    ]

    for i in range(2):
        for users_set in db.fetchmany("""
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
                    AND utc.start_date < NOW() - interval '{tariff_duration_days} day'
            ) AS subscription_filter ON (u.id = subscription_filter.user_id)
            WHERE
                utc.user_id = subscription_filter.user_id
            RETURNING u.id, u.service_id, u.language_code, subscription_filter.prolongable, utc.tariff_id
        """.format(
            update_action=update_actions[i], tariff_duration_days=constants.tariff_duration_days,
            prolongable_condition=prolongable_conditions[i]
        ), 100):

            for user in users_set:
                update_user_moderated_chats(user['id'], tariffs[user['tariff_id']]['channels_count'])

                yield {
                    'user': {
                        'id': user['id'],
                        'service_id': user['service_id'],
                        'language_code': user['language_code']
                    },
                    'action': 'disabled' if i == 0 else 'prolonged',
                    'prolongable': user['prolongable']
                }


def update_user_moderated_chats(user_id: int, offset: int | None):
    # All enabled
    if offset is None:
        db.execute("""
            UPDATE moderated_chats AS mc
            SET disabled = FALSE
            FROM user_moderated_chat_connections AS umcc
            WHERE
                umcc.moderated_chat_id = mc.id
                AND umcc.user_id = %s
                AND umcc.owner IS TRUE
        """, (user_id,))
        return

    cursor = db.build_cursor()

    # Disable after offset
    db.execute("""
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
    """, (user_id, offset,), commit=False, cursor=cursor)

    # Enable before offset
    db.execute("""
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
    """, (user_id, offset,), cursor=cursor)
