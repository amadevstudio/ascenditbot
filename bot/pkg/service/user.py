from pkg.repository import user_repository
from pkg.service.service import Service
from project.types import UserInterface


class User(Service):
    @staticmethod
    def register(chat_id: int, language_code: str) -> None:
        user: UserInterface = {"service_id": str(chat_id), "language_code": language_code}

        user_repository.register_or_update_by_service_id(user)
        # TODO: referral program for user.register
        # TODO: free subscription for 2 weeks

    # TODO: Analytics on every income message
    # def in_message(chat_id: int):
    #     pass
    @staticmethod
    def get_id_by_service_id(chat_id: int) -> int | None:
        return user_repository.get_id_by_service_id(str(chat_id))

