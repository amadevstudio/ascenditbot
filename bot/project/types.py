import datetime
from typing import TypedDict


class ErrorDictInterface(TypedDict, total=False):
    error: str


class UserInterface(TypedDict, total=False):
    id: int
    service_id: str
    language_code: str
    ref_id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime


class ChatInterface(TypedDict, total=False):
    id: int
    service_id: str
    active: bool
    disabled: bool
    allow_administrators: bool
    allowed_keywords: str
    created_at: datetime.datetime
    updated_at: datetime.datetime


class AllowedUserInterface(TypedDict, total=False):
    id: int
    moderated_chat_id: int
    nickname: str
    active: bool
    images_allowed: bool
    links_allowed: bool
    period_quantity: int
    period_type: str
    period_quantity_left: int
    ban_expiration_date: datetime.datetime
    created_at: datetime.datetime
    updated_at: datetime.datetime


class TariffInterface(TypedDict, total=False):
    id: int
    channels_count: int
    created_at: datetime.datetime
    updated_at: datetime.datetime


class TariffPriceInterface(TypedDict, total=False):
    tariff_id: int
    currency_code: str
    price: int
    created_at: datetime.datetime
    updated_at: datetime.datetime


class UserTariffConnectionInterface(TypedDict, total=False):
    user_id: int
    tariff_id: int
    balance: int
    currency_code: str
    start_date: datetime.datetime | None
    created_at: datetime.datetime
    updated_at: datetime.datetime


class PaymentHistoryInterface(TypedDict, total=False):
    id: int
    user_id: int
    payment_service: str
    status: int
    amount: int
    currency_code: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
