import datetime
from typing import TypedDict

from pkg.repository import allowed_user_repository


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


# allowed_user_interface = AllowedUserInterface.__annotations__


class AllowedUser:
    @staticmethod
    def find(allowed_user_id: int) -> AllowedUserInterface | None:
        return allowed_user_repository.find(allowed_user_id)

    @staticmethod
    def switch_active(allowed_user_id: int) -> bool | None:
        return allowed_user_repository.switch_active(allowed_user_id)

    @staticmethod
    def delete(allowed_user_id: int) -> int | None:
        return allowed_user_repository.delete(allowed_user_id)
