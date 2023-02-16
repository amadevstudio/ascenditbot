import datetime

from lib.language import localization
from pkg.repository.tariff_repository import UserTariffInfoInterface
from pkg.service.tariff import Tariff
from project import constants


def build_subscription_info_short(user_tariff_info: UserTariffInfoInterface | None, language_code: str) -> str:
    info_message = localization.get_message(
        ['tariffs', 'list', 'wrapper'], language_code,
        tariff_text=localization.get_message(['tariffs', 'list', user_tariff_info['tariff_id']], language_code))

    days_left_message = build_days_left_message(user_tariff_info['end_date'], language_code)
    if days_left_message is not None:
        info_message += ", " + days_left_message.lower()

    cant_renew_message = build_cant_renew_message(user_tariff_info, language_code)
    if cant_renew_message is not None:
        info_message += "\n" + cant_renew_message

    return info_message


def build_subscription_info(user_tariff_info: UserTariffInfoInterface | None, language_code: str) -> str:
    tariff_name = localization.get_message(['tariffs', 'list', user_tariff_info['tariff_id']], language_code)
    info_message = f"{tariff_name}"

    balance = Tariff.user_amount(user_tariff_info['balance'])

    info_message += f"\n{localization.get_message(['subscription', 'info_block', 'balance'], language_code)} " \
                    f"{balance} {user_tariff_info['currency_code']}"

    cant_renew_message = build_cant_renew_message(user_tariff_info, language_code)
    if cant_renew_message is not None:
        info_message += "\n" + cant_renew_message

    days_left_message = build_days_left_message(user_tariff_info['end_date'], language_code)
    if days_left_message is not None:
        info_message += "\n" + days_left_message

    info_message += "\n" + channels_count_text(user_tariff_info['channels_count'], language_code)

    return info_message


def build_days_left_message(end_date: datetime.datetime, language_code: str) -> str | None:
    if end_date is not None:
        days_left = (
                end_date
                - datetime.datetime.now()
        ).days + 1

        if days_left == 1:
            return localization.get_message(
                ['subscription', 'info_block', 'less_than_one_day'], language_code)

        return localization.get_numerical_declension_message(
            ['subscription', 'info_block', 'days_left'], language_code,
            days_left if days_left >= 0 else 0, days_left=days_left)


def build_cant_renew_message(user_tariff_info: UserTariffInfoInterface, language_code: str) -> str | None:
    if user_tariff_info['tariff_id'] is None:
        return None

    if user_tariff_info['balance'] < user_tariff_info['price']:
        return localization.get_message(
            ['subscription', 'info_block', 'not_enough_for_renewal'], language_code)
    else:
        return None


def channels_count_text(channels_count: int, language_code: str) -> str:
    return (
        localization.get_message(['subscription', 'info_block', 'unlimited'], language_code)
        if channels_count is None
        else str(channels_count)
    ) + ' ' + localization.get_numerical_declension_message(
        ['subscription', 'info_block', 'of_channels'], language_code,
        5 if channels_count is None else channels_count)  # unlimited
