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
    email: str
    nickname: str
    is_admin: bool


class ModeratedChatInterface(TypedDict, total=False):
    id: int
    service_id: str
    active: bool
    disabled: bool
    allow_administrators: bool
    allowed_keywords: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    name: str
    restriction_duration_minutes: int


class UserModeratedChatConnectionInterface(TypedDict, total=False):
    id: int
    user_id: int
    owner: bool
    moderated_chat_id: int
    created_at: datetime.date
    updated_at: datetime.date


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
    id: int | None
    channels_count: int
    created_at: datetime.datetime
    updated_at: datetime.datetime


class TariffPriceInterface(TypedDict, total=False):
    tariff_id: int | None
    currency_code: str
    currency_title: str
    minor_units: int
    payment_provider: str
    price: int
    created_at: datetime.datetime
    updated_at: datetime.datetime


class TariffInfoInterface(TariffInterface, TariffPriceInterface):
    pass


class CurrencyInterface(TypedDict, total=False):
    code: str
    title: str
    minor_units: int
    payment_provider: str
    enabled: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime


class UserBalanceInterface(TypedDict, total=False):
    user_id: int
    currency_code: str
    currency_title: str
    minor_units: int
    payment_provider: str
    balance: int
    created_at: datetime.datetime
    updated_at: datetime.datetime


class UserTariffConnectionInterface(TypedDict, total=False):
    user_id: int
    tariff_id: int | None
    payment_currency_code: str
    end_date: datetime.datetime | None
    trial_was_activated: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime


class PaymentHistoryInterface(TypedDict, total=False):
    id: int
    user_id: int
    payment_service: str
    status: int
    amount: int
    currency_code: str
    external_payment_id: str
    invoice_payload: str
    provider_out_sum: str
    provider_inc_sum: str
    provider_inc_curr_label: str
    provider_payment_method: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
