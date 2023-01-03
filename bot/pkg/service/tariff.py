import datetime

from lib.language import localization
from pkg.repository import tariff_repository
from pkg.repository.tariff_repository import UserTariffInfoInterface
from pkg.service.service import Service

from project import constants


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
    def build_tariff_info_message(tariff_info: UserTariffInfoInterface | None, language_code: str) -> str:
        tariff_name = localization.get_message(['subscription', 'tariffs', tariff_info['tariff_id']], language_code)
        info_message = f"{tariff_name}\n"
        info_message += f"{localization.get_message(['subscription', 'info_block', 'balance'], language_code)} " \
                        f"{tariff_info['balance']} {tariff_info['currency_code']}\n"

        if tariff_info['balance'] < tariff_info['price']:
            info_message += localization.get_message(
                ['subscription', 'info_block', 'not_enough_for_renewal'], language_code) + "\n"

        if tariff_info['start_date'] is not None:
            days_left = (
                    tariff_info['start_date'] + datetime.timedelta(days=constants.tariff_duration_days)
                    - datetime.datetime.now()
            ).days
            info_message += localization.get_numerical_declension_message(
                ['subscription', 'info_block', 'days_left'], language_code,
                days_left if days_left >= 0 else 0, days_left=days_left)

        info_message += (
           localization.get_message(['subscription', 'info_block', 'unlimited'], language_code)
           if tariff_info['channels_count'] == -1
           else str(tariff_info['channels_count'])
        ) + ' ' + localization.get_numerical_declension_message(
            ['subscription', 'info_block', 'of_channels'], language_code,
            5 if tariff_info['channels_count'] == -1 else tariff_info['channels_count'])  # unlimited
        return info_message
