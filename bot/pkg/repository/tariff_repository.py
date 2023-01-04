import datetime
from typing import TypedDict

from pkg.repository.database_connection import Database
from project.types import TariffInterface, TariffPriceInterface

db = Database()


class UserTariffInfoInterface(TypedDict, total=True):
    channels_count: int
    currency_code: str
    price: int
    balance: int
    start_date: datetime.datetime | None
    user_id: int
    tariff_id: int


class TariffInfoInterface(TariffInterface, TariffPriceInterface):
    pass


def user_tariff_info(user_id: int) -> UserTariffInfoInterface | None:
    return db.fetchone("""
        SELECT t.channels_count, tp.currency_code, tp.price,
            utc.balance, utc.start_date, utc.user_id, utc.tariff_id
        FROM user_tariff_connections AS utc
        INNER JOIN tariffs AS t ON (t.id = utc.tariff_id)
        LEFT JOIN users AS u ON (u.id = utc.user_id)
        LEFT JOIN lang_country_curr_codes AS lccc ON (lccc.language_code = u.language_code)
        INNER JOIN tariff_prices AS tp ON (
            tp.tariff_id = t.id
            AND (
                tp.currency_code = utc.currency_code
                OR (tp.currency_code = lccc.currency_code AND utc.currency_code IS NULL)
                OR (tp.currency_code = 'usd' AND utc.currency_code IS NULL AND lccc.currency_code IS NULL)
            )
        )
        WHERE utc.user_id = %s
    """, (user_id,))


# def tariffs() -> list[TariffInterface]:
#     return db.fetchall("SELECT * FROM tariffs")


def tariffs_info(user_id: int) -> list[TariffInfoInterface]:
    return db.fetchall("""
        SELECT t.id, t.channels_count, tp.currency_code, tp.price
        FROM tariffs AS t
        LEFT JOIN user_tariff_connections AS utc ON (utc.tariff_id = t.id)
        LEFT JOIN users AS u ON (u.id = %s)
        LEFT JOIN lang_country_curr_codes AS lccc ON (lccc.language_code = u.language_code)
        INNER JOIN tariff_prices AS tp ON (
            t.id = tp.tariff_id
            AND (
                tp.currency_code = utc.currency_code
                OR (tp.currency_code = lccc.currency_code AND utc.currency_code IS NULL)
                OR (tp.currency_code = 'usd' AND utc.currency_code IS NULL AND lccc.currency_code IS NULL)
            )
        )
        ORDER BY t.id ASC
    """, (user_id,))
