from typing import TypedDict

from pkg.repository import user_repository
from pkg.service.service import Service
from pkg.service.tariff import Tariff
from pkg.service.user_storage import UserStorage
from pkg.system.logger import logger
from project import constants
from project.types import UserInterface, UserTariffConnectionInterface


class RegistrationResultInterface(TypedDict, total=False):
    user: UserInterface | None
    refer: UserInterface | None
    subscription: UserTariffConnectionInterface | None


class BeginParamsInterface(TypedDict, total=False):
    referral: str | None


class User(Service):
    @staticmethod
    def register(chat_id: int, language_code: str, initial_data: BeginParamsInterface) -> RegistrationResultInterface:
        user: UserInterface = {"service_id": str(chat_id), "language_code": language_code}

        registration_result = user_repository.register_or_update_by_service_id(
            user, referral_service_id=initial_data['referral'])

        result: RegistrationResultInterface = {'user': registration_result['user']}

        if registration_result['is_new'] and registration_result['user']['ref_id'] is not None:
            result = {**result, 'refer': User.get_by_id(registration_result['user']['ref_id'])}

        tariff_initiation_result = Tariff.initiate(registration_result['user']['id'])
        result = {**result, 'subscription': tariff_initiation_result}

        return result

    @classmethod
    def bot_is_blocked(cls, chat_id: int):
        user_id = User.get_id_by_service_id(chat_id)
        Tariff.change(user_id, 0, force=True)

        UserStorage.clear_storage(chat_id)

        # TODO: add block flag?

    # TODO: Analytics on every income message
    # def in_message(chat_id: int):
    #     pass

    @staticmethod
    def get_by_id(user_id: int) -> UserInterface | None:
        return user_repository.find_by({'id': user_id})

    @staticmethod
    def get_id_by_service_id(user_chat_id: int) -> int | None:
        return user_repository.get_id_by_service_id(str(user_chat_id))

    @staticmethod
    def find_by_service_id(user_chat_id: int) -> UserInterface | None:
        return user_repository.find_by({'service_id': str(user_chat_id)})

    @staticmethod
    def update_email_by_service_id(user_chat_id: int, email: str) -> UserInterface:
        return user_repository.update_by_service_id(str(user_chat_id), {'email': email})

    @staticmethod
    def generate_referral_link(user_chat_id: int) -> str:
        return f"t.me/{constants.bot_nickname}?start=referral_{user_chat_id}"

    @staticmethod
    def analyze_initial_data(initial_text: str) -> BeginParamsInterface:
        params_string = initial_text[7:]
        params: BeginParamsInterface = {
            'referral': None
        }
        try:
            string_params = params_string.split('/')
            for param_pair in string_params:
                if '_' not in param_pair:
                    continue

                param_name, param_value = param_pair.split('_')
                params = {**params, param_name: param_value}

        except Exception as e:
            logger.error(e)

        return params
