import datetime

from lib.python.dict_interface import validate_structure
from pkg.repository import user_repository


user_interface = {
    'id': int,
    'service_id': str,
    'language_code': str,
    'ref_id': int,
    'created_at': datetime.datetime,
    'updated_at': datetime.datetime
}


class User:
    @staticmethod
    def register(chat_id: int, language_code: str):
        user = {"service_id": str(chat_id), "language_code": language_code}
        if not validate_structure(user, user_interface):
            return False

        user_repository.register_or_update_by_service_id(user)
        # TODO: referral program for user.register
        # TODO: free subscription for 2 weeks


    # TODO: Analytics on every income message
    # def in_message(chat_id: int):
    #     pass
