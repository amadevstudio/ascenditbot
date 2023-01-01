from pkg.repository import allowed_user_repository, chat_repository
from pkg.service.service import Service
from project.types import AllowedUserInterface


# allowed_user_interface = AllowedUserInterface.__annotations__


class AllowedUser(Service):
    @staticmethod
    def find(allowed_user_id: int) -> AllowedUserInterface | None:
        return allowed_user_repository.find(allowed_user_id)

    @staticmethod
    def switch_active(allowed_user_id: int) -> bool | None:
        return allowed_user_repository.switch_active(allowed_user_id)

    @staticmethod
    def delete(allowed_user_id: int) -> int | None:
        return allowed_user_repository.delete(allowed_user_id)

    @staticmethod
    def check_privilege(nickname: str, chat_service_id: str) -> bool:
        chat_monitoring_active: bool = chat_repository.is_active_by_service_id(str(chat_service_id))
        if not chat_monitoring_active:
            return True

        privileges: AllowedUserInterface | None = allowed_user_repository.get_privileges(nickname, chat_service_id)
        if privileges is None:
            return False

        able_to_write = privileges['active']
        # TODO: add more filters: images, ban period etc
        return able_to_write
