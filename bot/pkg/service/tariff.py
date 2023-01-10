import datetime

from lib.language import localization
from pkg.repository import tariff_repository
from pkg.repository.tariff_repository import UserTariffInfoInterface, TariffInfoInterface
from pkg.service.service import Service

from project import constants
from project.types import UserTariffConnectionInterface, ErrorDictInterface


class Tariff(Service):
    @staticmethod
    def user_tariff_info(user_id: int) -> UserTariffInfoInterface:
        tariff_info = tariff_repository.user_tariff_info(user_id)
        if tariff_info is None:
            tariff_info: UserTariffInfoInterface = {
                'channels_count': 0,
                'currency_code': '',
                'price': 0,
                'balance': 0,
                'start_date': None,
                'user_id': user_id,
                'tariff_id': 0
            }

        return tariff_info

    @staticmethod
    def build_subscription_info_short(user_tariff_info: UserTariffInfoInterface | None, language_code: str) -> str:
        info_message = localization.get_message(['tariffs', 'list', user_tariff_info['tariff_id']], language_code)
        info_message += Tariff._cant_renew_message_info_part(user_tariff_info, language_code)
        return info_message

    @staticmethod
    def build_subscription_info(user_tariff_info: UserTariffInfoInterface | None, language_code: str) -> str:
        tariff_name = localization.get_message(['tariffs', 'list', user_tariff_info['tariff_id']], language_code)
        info_message = f"{tariff_name}"

        balance = float(user_tariff_info['balance']) / 100
        info_message += f"\n{localization.get_message(['subscription', 'info_block', 'balance'], language_code)} " \
                        f"{balance} {user_tariff_info['currency_code']}"

        info_message += Tariff._cant_renew_message_info_part(user_tariff_info, language_code)

        if user_tariff_info['start_date'] is not None:
            days_left = (
                    user_tariff_info['start_date'] + datetime.timedelta(days=constants.tariff_duration_days)
                    - datetime.datetime.now()
            ).days
            info_message += "\n" + localization.get_numerical_declension_message(
                ['subscription', 'info_block', 'days_left'], language_code,
                days_left if days_left >= 0 else 0, days_left=days_left)

        info_message += "\n" + Tariff._channels_count_text(user_tariff_info['channels_count'], language_code)

        return info_message

    @staticmethod
    def _cant_renew_message_info_part(user_tariff_info: UserTariffInfoInterface, language_code: str) -> str:
        if user_tariff_info['balance'] < user_tariff_info['price']:
            return "\n" + localization.get_message(
                ['subscription', 'info_block', 'not_enough_for_renewal'], language_code)
        else:
            return ''

    @staticmethod
    def _channels_count_text(channels_count: int, language_code: str) -> str:
        return (
            localization.get_message(['subscription', 'info_block', 'unlimited'], language_code)
            if channels_count is None
            else str(channels_count)
        ) + ' ' + localization.get_numerical_declension_message(
            ['subscription', 'info_block', 'of_channels'], language_code,
            5 if channels_count is None else channels_count)  # unlimited

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

        best_tariff = Tariff.tariffs_info(user_id).pop()

        subscription: UserTariffConnectionInterface = {
            'user_id': user_id,
            'tariff_id': best_tariff['id'],
            'balance': 0,
            'currency_code': best_tariff['currency_code'],
            'start_date':
                datetime.datetime.now()
                - datetime.timedelta(days=(constants.tariff_duration_days - constants.tariff_free_trail_days)),
        }

        return tariff_repository.update_subscription(subscription)
