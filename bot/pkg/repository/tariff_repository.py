import datetime
from typing import TypedDict

from pkg.repository.database_connection import Database
from project.constants import default_currency
from project.types import TariffInterface, UserTariffConnectionInterface, TariffInfoInterface

db = Database()


class UserTariffInfoInterface(TypedDict, total=True):
    channels_count: int
    currency_code: str
    price: int
    balance: int
    start_date: datetime.datetime | None
    user_id: int
    tariff_id: int | None


def find(tariff_id: int) -> TariffInterface | None:
    return db.find_model('tariffs', {'id': tariff_id})


def _tariff_prices_for_user_selection() -> str:
    return """
        AND (
            (tp.currency_code = utc.currency_code
                OR (tp.currency_code = lccc.currency_code AND utc.currency_code IS NULL)
                OR (tp.currency_code = 'usd' AND utc.currency_code IS NULL AND lccc.currency_code IS NULL)
            )
            OR tp.currency_code IS NULL
        )
    """


def tariff_info(tariff_id: int, user_id: int) -> TariffInfoInterface | None:
    return db.fetchone(f"""
        SELECT t.id, t.channels_count, tp.currency_code, tp.price
        FROM tariffs AS t
        LEFT JOIN user_tariff_connections AS utc ON (utc.tariff_id = t.id)
        LEFT JOIN users AS u ON (u.id = %s)
        LEFT JOIN lang_country_curr_codes AS lccc ON (lccc.language_code = u.language_code)
        INNER JOIN tariff_prices AS tp ON (
            t.id = tp.tariff_id
            -- Take currency from user if connection not exists only
            {_tariff_prices_for_user_selection()}
        )
        WHERE t.id = %s
    """, (user_id, tariff_id,))


def tariffs_info(user_id: int) -> list[TariffInfoInterface | None]:
    return db.fetchall(f"""
        SELECT t.id, t.channels_count, tp.currency_code, tp.price
        FROM tariffs AS t
        LEFT JOIN user_tariff_connections AS utc ON (utc.tariff_id = t.id)
        LEFT JOIN users AS u ON (u.id = %s)
        LEFT JOIN lang_country_curr_codes AS lccc ON (lccc.language_code = u.language_code)
        INNER JOIN tariff_prices AS tp ON (
            t.id = tp.tariff_id
            -- Take currency from user if connection not exists only
            {_tariff_prices_for_user_selection()}
        )
        ORDER BY t.id ASC
    """, (user_id,))


def update_subscription(subscription: UserTariffConnectionInterface) -> UserTariffConnectionInterface:
    return db.insert_model(
        'user_tariff_connections', subscription,
        conflict_unique_fields=['user_id'])


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
            -- Take currency from user if connection not exists only
            {_tariff_prices_for_user_selection()}
        )
        WHERE utc.user_id = %s
    """, (user_id,))


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
    x = db.fetchone("""
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
            GROUP BY umcc.user_id
        ) AS user_chats_stat ON (user_chats_stat.user_id = u.id)
        INNER JOIN user_tariff_connections AS utc ON (utc.user_id = u.id)
        INNER JOIN tariffs AS t ON (t.id = utc.tariff_id)
        WHERE u.service_id = %s;
    """, (chat_id,))['satisfies']
    print("HERE", x)
    return x
