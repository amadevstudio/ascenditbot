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
                "states": "users:{chat_id}:states",
                "state_data": "users:{chat_id}:state_data",
                "resend_flag": "users:{chat_id}:resend_flag",
                "message_structures": "users:{chat_id}:message_structures"
            }
        }
    }
}


def clear_user_storage(chat_id):
    storage_key_values = get_all_level_values(STORAGE_KEYS)

    for key in storage_key_values:
        Storage().connection.delete(key.format(chat_id=chat_id))


# User states

@convert_bytes_to_strings
def get_user_states(chat_id):
    return Storage().connection.lrange(STORAGE_KEYS["users"]["tg"]["@id"]["states"].format(chat_id=chat_id), 0, -1)


@convert_bytes_to_strings
def get_user_curr_state(chat_id):
    return Storage().connection.lindex(STORAGE_KEYS["users"]["tg"]["@id"]["states"].format(chat_id=chat_id), -1)


@convert_bytes_to_strings
def get_user_prev_state(chat_id):
    return Storage().connection.lindex(STORAGE_KEYS["users"]["tg"]["@id"]["states"].format(chat_id=chat_id), -2)


@convert_bytes_to_strings
def get_user_prev_curr_states(chat_id):
    return Storage().connection.lrange(STORAGE_KEYS["users"]["tg"]["@id"]["states"].format(chat_id=chat_id), -2, -1)


@convert_bytes_to_strings
def get_user_state_data(chat_id, state):
    state_data = Storage().connection.hget(
        STORAGE_KEYS["users"]["tg"]["@id"]["state_data"].format(chat_id=chat_id), state)
    if state_data is None:
        return {}

    return json.loads(state_data)


def add_user_state(chat_id, state):
    return Storage().connection.rpush(STORAGE_KEYS["users"]["tg"]["@id"]["states"].format(chat_id=chat_id), state)


def add_user_state_data(chat_id, state, data):
    return Storage().connection.hset(
        STORAGE_KEYS["users"]["tg"]["@id"]["state_data"].format(chat_id=chat_id), state, json.dumps(data))


def del_user_curr_state(chat_id):
    return Storage().connection.rpop(STORAGE_KEYS["users"]["tg"]["@id"]["states"].format(chat_id=chat_id))


def del_user_states(chat_id):
    return Storage().connection.delete(STORAGE_KEYS["users"]["tg"]["@id"]["states"].format(chat_id=chat_id))


def del_user_state_data(chat_id, state):
    return Storage().connection.hdel(STORAGE_KEYS["users"]["tg"]["@id"]["state_data"].format(chat_id=chat_id), state)


# Resend flag

@convert_bytes_to_strings
def get_user_resend_flag(chat_id):
    return Storage().connection.get(STORAGE_KEYS["users"]["tg"]["@id"]["resend_flag"].format(chat_id=chat_id)) == "1"


# Last message text id

@convert_bytes_to_strings
def get_user_message_structures(chat_id):
    message_structures = Storage().connection.get(
        STORAGE_KEYS["users"]["tg"]["@id"]["message_structures"].format(chat_id=chat_id))
    if message_structures is None:
        return []

    message_structures_decoded = json.loads(message_structures)
    for message_structure in message_structures_decoded:
        message_structure['id'] = int(message_structure['id'])

    return message_structures_decoded


def set_user_message_structures(chat_id: int, message_structures: list[dict]):
    return Storage().connection.set(
        STORAGE_KEYS["users"]["tg"]["@id"]["message_structures"].format(chat_id=chat_id),
        json.dumps(message_structures))
