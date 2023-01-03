import datetime
from typing import TypedDict

from pkg.repository.database_connection import Database
from project.types import TariffInterface, TariffPriceInterface, UserTariffConnectionInterface

db = Database()


class UserTariffInfoInterface(TypedDict, total=True):
    channels_count: int
    currency_code: str
    price: int
    balance: int
    start_date: datetime.datetime
    user_id: int
    tariff_id: int


def user_tariff_info(user_id: int) -> UserTariffInfoInterface | None:
    return db.fetchone("""
        SELECT t.channels_count, tp.currency_code, tp.price,
            utc.balance, utc.start_date, utc.user_id, utc.tariff_id
        FROM user_tariff_connections AS utc
        INNER JOIN tariffs AS t ON (t.id = utc.tariff_id)
        INNER JOIN tariff_prices AS tp ON (
            tp.tariff_id = t.id
            AND (
                tp.currency_code = utc.currency_code
                OR (tp.currency_code = 'usd' AND tp.currency_code != utc.currency_code)
            )
        )
        WHERE utc.user_id = %s
    """, (user_id,))
