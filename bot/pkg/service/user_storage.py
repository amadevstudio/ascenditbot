import json
from typing import Dict

from pkg.config import routes
from pkg.repository import user_storage_repository


class UserStorage:
    @staticmethod
    def new_navigation_journey(chat_id: int, initial_page: str):
        user_storage_repository.del_user_states(chat_id)
        user_storage_repository.add_user_state(chat_id, initial_page)

    @staticmethod
    def change_page(service_chat_id: int, state: str, data: dict[str, any] = None):
        curr_state = user_storage_repository.get_user_curr_state(service_chat_id)
        if curr_state == state:
            return

        user_storage_repository.add_user_state(service_chat_id, state)
        if data is not None:
            user_storage_repository.add_user_state_data(service_chat_id, state, data)

    @staticmethod
    def go_back(chat_id: int, state: str = None):
        user_storage_repository.del_user_curr_state(chat_id)
        if state is not None:
            user_storage_repository.del_user_state_data(chat_id, state)

    @staticmethod
    def curr_state(chat_id: int):
        return user_storage_repository.get_user_curr_state(chat_id)

    @staticmethod
    def get_user_prev_state(chat_id: int):
        return user_storage_repository.get_user_curr_state(chat_id)

    @staticmethod
    def prev_curr_states(chat_id: int):
        states = user_storage_repository.get_user_prev_curr_states(chat_id)
        if isinstance(states, list):
            if len(states) == 2:
                return states
            elif len(states) == 1:
                return None, states[0]
            else:
                return None, routes.RouteMap.main_route()
        else:
            return None, states

    @staticmethod
    def all_states(chat_id: int):
        return user_storage_repository.get_user_states(chat_id)

    @staticmethod
    def should_resend(chat_id: int):
        return user_storage_repository.get_user_resend_flag(chat_id)

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
    def add_user_state_data(chat_id: int, state: str, state_data: dict):
        user_storage_repository.add_user_state_data(chat_id, state, state_data)
