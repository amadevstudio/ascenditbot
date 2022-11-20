import json

import redis

from lib.python.data_helper import get_all_level_values
from pkg.repository.storage_connection import Storage
from lib.redis.decorators import convert_bytes_to_strings


storage = Storage()

STORAGE_KEYS = {
    "users": {
        "tg": {
            "@id": {
                "states": "users:@{user_id}:states",
                "state_data": "users:@{user_id}:state_data"
            }
        }
    }
}


def clear_user_storage(user_id):
    storage_key_values = get_all_level_values(STORAGE_KEYS)

    for key in storage_key_values:
        Storage().connection.delete(key.format)


# User states

@convert_bytes_to_strings
def get_user_states(user_id):
    return Storage().connection.lrange(STORAGE_KEYS["users"]["tg"]["@id"]["states"].format(user_id=user_id), 0, -1)


@convert_bytes_to_strings
def get_user_curr_state(user_id):
    return Storage().connection.lindex(STORAGE_KEYS["users"]["tg"]["@id"]["states"].format(user_id=user_id), -1)


@convert_bytes_to_strings
def get_user_prev_state(user_id):
    return Storage().connection.lindex(STORAGE_KEYS["users"]["tg"]["@id"]["states"].format(user_id=user_id), -2)


@convert_bytes_to_strings
def get_user_prev_curr_states(user_id):
    return Storage().connection.lrange(STORAGE_KEYS["users"]["tg"]["@id"]["states"].format(user_id=user_id), -2, -1)


@convert_bytes_to_strings
def get_user_state_data(user_id, state):
    return json.loads(Storage().connection.hget(
        STORAGE_KEYS["users"]["tg"]["@id"]["state_data"].format(user_id=user_id), state))


def add_user_state(user_id, state):
    return Storage().connection.rpush(STORAGE_KEYS["users"]["tg"]["@id"]["states"].format(user_id=user_id), state)


def add_user_state_data(user_id, state, data):
    return Storage().connection.hset(
        STORAGE_KEYS["users"]["tg"]["@id"]["state_data"].format(user_id=user_id), state, json.dumps(data))


def del_user_curr_state(user_id):
    return Storage().connection.lpop(STORAGE_KEYS["users"]["tg"]["@id"]["states"].format(user_id=user_id))


def del_user_states(user_id):
    return Storage().connection.delete(STORAGE_KEYS["users"]["tg"]["@id"]["states"].format(user_id=user_id))
