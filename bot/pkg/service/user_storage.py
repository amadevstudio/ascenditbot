import json
from typing import Dict

from pkg.repository import user_storage_repository


def new_navigation_journey(chat_id: int, initial_page: str):
    user_storage_repository.del_user_states(chat_id)
    user_storage_repository.add_user_state(chat_id, initial_page)


def change_page(chat: int, state: str, data: dict[str, any] = None):
    user_storage_repository.add_user_state(chat, state)
    if data is not None:
        user_storage_repository.add_user_state_data(chat, state, data)


def go_back(chat_id: int):
    user_storage_repository.del_user_curr_state(chat_id)


def curr_state(chat_id: int):
    return user_storage_repository.get_user_curr_state(chat_id)


def get_user_prev_state(chat_id: int):
    return user_storage_repository.get_user_curr_state(chat_id)


def prev_curr_states(chat_id: int):
    states = user_storage_repository.get_user_prev_curr_states(chat_id)
    if isinstance(states, list):
        return states
    else:
        return None, states


def all_states(chat_id: int):
    return user_storage_repository.get_user_states(chat_id)


def should_resend(chat_id: int):
    return user_storage_repository.get_user_resend_flag(chat_id)


def get_message_structures(chat_id: int):
    return user_storage_repository.get_user_message_structures(chat_id)


def set_message_structures(chat_id: int, message_structures: list[dict]):
    user_storage_repository.set_user_message_structures(chat_id, message_structures)


def get_user_state_data(chat_id: int, state: str):
    return user_storage_repository.get_user_state_data(chat_id, state)


def add_user_state_data(chat_id: int, state: str, state_data: dict):
    user_storage_repository.add_user_state_data(chat_id, state, state_data)
