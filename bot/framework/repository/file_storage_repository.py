from framework.repository.storage_connection import Storage
from lib.redis.decorators import convert_bytes_to_strings

storage = Storage()

STORAGE_KEYS = {
    "telegram_files": {
        "files_id": "telegram_files:files_id"
    }
}


@convert_bytes_to_strings
def get_file_id(path: str) -> bytes | None:
    state_data = Storage().connection.hget(STORAGE_KEYS['telegram_files']['files_id'], path)
    return state_data


def add_file_id(path: str, file_id: str):
    return Storage().connection.hset(STORAGE_KEYS['telegram_files']['files_id'], path, file_id)
