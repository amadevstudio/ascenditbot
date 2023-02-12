from lib.language import localization
from pkg.service.tariff import Tariff
from pkg.template.tariff.common import build_subscription_info


def prolonged_message(user_id: int, language_code: str, prolongable: bool = True) -> str:
    message_text = localization.get_message(['subscription', 'updates', 'prolonged'], language_code)

    if prolongable is not True:
        message_text += "\n\n" + localization.get_message(['subscription', 'updates', 'non-prolongable'], language_code)

    user_tariff_info = Tariff.user_tariff_info(user_id)
    message_text += "\n\n" + localization.get_message(['tariffs', 'current'], language_code) \
                    + "\n" + build_subscription_info(user_tariff_info, language_code)
    return message_text


def disabled_message(user_id: int, language_code: str) -> str:
    message_text = localization.get_message(['subscription', 'updates', 'disabled'], language_code)

    user_tariff_info = Tariff.user_tariff_info(user_id)
    message_text += "\n\n" + localization.get_message(['tariffs', 'current'], language_code) \
                    + "\n" + build_subscription_info(user_tariff_info, language_code)

    return message_text


def remaining_days_left_message(user_id: int, language_code: str, days_left: int) -> str:
    message_text = localization.get_message(['subscription', 'updates', 'non-prolongable'], language_code)

    message_text += "\n\n" + localization.get_numerical_declension_message(
            ['subscription', 'info_block', 'days_left'], language_code,
            days_left if days_left >= 0 else 0, days_left=days_left)

    user_tariff_info = Tariff.user_tariff_info(user_id)
    message_text + "\n\n" + localization.get_message(['tariffs', 'current'], language_code) \
                   + "\n" + build_subscription_info(user_tariff_info, language_code)

    return message_text
