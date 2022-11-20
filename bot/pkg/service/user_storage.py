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


def prev_curr_states(user_id: int):
    return user_storage_repository.get_user_prev_curr_states(user_id)
