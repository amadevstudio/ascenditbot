from typing import Any

from framework.repository import user_storage_repository
from pkg.service.service import Service


class UserStorage(Service):
    @staticmethod
    def new_navigation_journey(chat_id: int, initial_page: str):
        user_storage_repository.del_user_states(chat_id)
        user_storage_repository.add_user_state(chat_id, initial_page)

    @staticmethod
    def change_page(chat_id: int, state: str, data: dict[str, Any] = None):
        curr_state = user_storage_repository.get_user_curr_state(chat_id)
        if curr_state == state:
            return

        user_storage_repository.add_user_state(chat_id, state)
        if data is not None:
            user_storage_repository.add_user_state_data(chat_id, state, data)

    @staticmethod
    def go_back(chat_id: int):
        user_storage_repository.del_user_curr_state(chat_id)

    @staticmethod
    def curr_state(chat_id: int):
        return user_storage_repository.get_user_curr_state(chat_id)

    @staticmethod
    def prev_state(chat_id: int):
        return user_storage_repository.get_user_prev_state(chat_id)

    @staticmethod
    def prev_curr_states(chat_id: int) -> tuple[str | None, str | None] | list:
        states = user_storage_repository.get_user_prev_curr_states(chat_id)
        if isinstance(states, list):
            if len(states) == 2:
                return states
            elif len(states) == 1:
                return None, states[0]
            else:
                return None, None
        else:
            return None, states

    @staticmethod
    def all_states(chat_id: int):
        return user_storage_repository.get_user_states(chat_id)

    @staticmethod
    def clear_storage(chat_id: int):
        user_storage_repository.clear_user_storage(chat_id)

    @staticmethod
    def should_resend(chat_id: int) -> bool:
        return user_storage_repository.get_user_resend_flag(chat_id) == '1'

    @staticmethod
    def set_resend(chat_id: int, resend: bool = True):
        if resend is False:
            user_storage_repository.del_user_resend_flag(chat_id)

        resend_num = 1 if resend else 0

        user_storage_repository.set_user_resend_flag(chat_id, resend_num)

    @staticmethod
    def get_message_structures(chat_id: int):
        return user_storage_repository.get_user_message_structures(chat_id)

    @staticmethod
    def set_message_structures(chat_id: int, message_structures: list[dict]):
        user_storage_repository.set_user_message_structures(chat_id, message_structures)

    @staticmethod
    def get_user_state_data(chat_id: int, state: str):
        return user_storage_repository.get_user_state_data(chat_id, state)

    @staticmethod
    def add_user_state_data(chat_id: int, state: str, state_data: dict[str, any]):
        user_storage_repository.add_user_state_data(chat_id, state, state_data)

    @staticmethod
    def del_user_state_data(chat_id: int, state: str):
        user_storage_repository.del_user_state_data(chat_id, state)
