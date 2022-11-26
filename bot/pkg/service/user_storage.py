import json
from typing import Dict

from pkg.repository import user_storage_repository


def new_navigation_journey(user_id: int, initial_page: str):
    user_storage_repository.del_user_states(user_id)
    user_storage_repository.add_user_state(user_id, initial_page)


def change_page(user_id: int, state: str, data: dict[str, any] = None):
    user_storage_repository.add_user_state(user_id, state)
    if data is not None:
        user_storage_repository.add_user_state_data(user_id, state, data)


def go_back(user_id: int):
    user_storage_repository.del_user_curr_state(user_id)


def curr_state(user_id: int):
    return user_storage_repository.get_user_curr_state(user_id)


def prev_curr_states(user_id: int):
    states = user_storage_repository.get_user_prev_curr_states(user_id)
    if isinstance(states, list):
        return states
    else:
        return None, states


def all_states(user_id: int):
    return user_storage_repository.get_user_states(user_id)


def should_resend(user_id: int):
    return user_storage_repository.get_user_resend_flag(user_id)


def get_message_structures(user_id: int):
    return user_storage_repository.get_user_message_structures(user_id)


def set_message_structures(user_id: int, message_structures: Dict):
    user_storage_repository.set_user_message_structures(user_id, message_structures)
