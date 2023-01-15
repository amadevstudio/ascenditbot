import datetime

from lib.language import localization
from pkg.repository import tariff_repository
from pkg.repository.tariff_repository import UserTariffInfoInterface, TariffInfoInterface
from pkg.service.service import Service
from pkg.system.logger import logger

from project import constants
from project.types import UserTariffConnectionInterface, ErrorDictInterface


class Tariff(Service):
    @staticmethod
    def tariff_info(tariff_id: int, user_id: int) -> TariffInfoInterface:
        tariff_info = tariff_repository.tariff_info(tariff_id, user_id)

        if tariff_info is None:
            user_base_currency_code = tariff_repository.get_currency_code_for_user(user_id)
            tariff_info: TariffInfoInterface = {
                'id': 0,
                'channels_count': 0,
                'currency_code': user_base_currency_code,
                'price': 0
            }

        return tariff_info

    @staticmethod
    def user_tariff_info(user_id: int) -> UserTariffInfoInterface:
        tariff_info = tariff_repository.user_tariff_info(user_id)
        if tariff_info is None:
            user_base_currency_code = tariff_repository.get_currency_code_for_user(user_id)
            tariff_info: UserTariffInfoInterface = {
                'channels_count': 0,
                'currency_code': user_base_currency_code,
                'price': 0,
                'balance': 0,
                'start_date': None,
                'user_id': user_id,
                'tariff_id': 0
            }

        return tariff_info

    # @staticmethod
    # def tariffs() -> list[TariffInterface]:
    #     return tariff_repository.tariffs()

    @staticmethod
    def tariffs_info(user_id: int) -> list[TariffInfoInterface]:
        return tariff_repository.tariffs_info(user_id)

    @staticmethod
    def find(tariff_id: int) -> TariffInfoInterface | None:
        return tariff_repository.find(tariff_id)

    @staticmethod
    def activate_trial(user_id: int) -> None | UserTariffConnectionInterface:
        tariff_info = tariff_repository.user_tariff_info(user_id)
        if tariff_info is not None:
            return None

        trial_tariff = Tariff.tariff_info(constants.tariff_free_trail_id, user_id)

        subscription: UserTariffConnectionInterface = {
            'user_id': user_id,
            'tariff_id': trial_tariff['id'],
            'balance': 0,
            'currency_code': trial_tariff['currency_code'],
            'start_date':
                datetime.datetime.now()
                - datetime.timedelta(days=(constants.tariff_duration_days - constants.tariff_free_trail_days)),
        }

        return tariff_repository.update_subscription(subscription)

    @staticmethod
    def change(user_id: int, chosen_tariff_id: int) -> UserTariffConnectionInterface | ErrorDictInterface:
        user_subscription = Tariff.user_tariff_info(user_id)
        if user_subscription['tariff_id'] == chosen_tariff_id:
            return {'error': 'already_chosen'}

        chosen_tariff = Tariff.tariff_info(chosen_tariff_id, user_id)
        user_tariff = Tariff.tariff_info(user_subscription['tariff_id'], user_id)

        # How many the user must pay
        if user_subscription['start_date'] is None:
            change_sum = chosen_tariff['price']
        else:
            # Do not take into account the current day, since part of it has passed, charge again
            days_left = constants.tariff_duration_days \
                        - (datetime.datetime.now() - user_subscription['start_date']).days
            if days_left > 0:
                # Change sum is positive when chosen tariff is more expensive
                change_sum = int(
                    (days_left / constants.tariff_duration_days) * chosen_tariff['price']
                    - ((days_left - 1) / constants.tariff_duration_days) * user_tariff['price']
                )
            else:
                change_sum = chosen_tariff['price']

        # Can the user pay for the best tariff?
        if change_sum > 0 and user_subscription['balance'] < change_sum:
            return {'error': 'not_enough_balance'}

        if chosen_tariff['id'] == 0:
            new_subscription_start_date = None
        else:
            new_subscription_start_date = \
                user_subscription['start_date'] if user_subscription['start_date'] is not None \
                else datetime.datetime.now()

        new_subscription: UserTariffConnectionInterface = {
            'user_id': user_id,
            'tariff_id': chosen_tariff['id'],
            'balance': user_subscription['balance'] - change_sum,
            'currency_code': user_subscription['currency_code'],
            'start_date': new_subscription_start_date,
        }

        return tariff_repository.update_subscription(new_subscription)

    @staticmethod
    def chats_number_satisfactory(chat_id: int) -> bool:
        return tariff_repository.chats_number_satisfactory(str(chat_id))
