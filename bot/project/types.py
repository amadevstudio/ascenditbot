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
