import datetime
from typing import Generator

from pkg.repository import tariff_repository
from pkg.repository.tariff_repository import UserTariffInfoInterface, TariffInfoInterface, ProcessSubscriptionInterface
from pkg.service.service import Service

from project import constants
from project.types import UserTariffConnectionInterface, ErrorDictInterface, PaymentHistoryInterface, UserInterface


class Tariff(Service):
    @staticmethod
    async def tariff_info(tariff_id: int, user_id: int) -> TariffInfoInterface:
        tariff_info = await tariff_repository.tariff_info(tariff_id, user_id)

        if tariff_info is None:
            user_base_currency_code = await tariff_repository.get_currency_code_for_user(user_id)
            tariff_info: TariffInfoInterface = {
                'id': 0,
                'channels_count': 0,
                'currency_code': user_base_currency_code,
                'price': 0
            }

        return tariff_info

    @staticmethod
    def user_amount(price: int, accuracy: int = 0, ndigits: int = 2) -> float:
        rounded = round((int(price) + int(accuracy)) / 100, ndigits)
        integer_value = int(rounded)
        if rounded == integer_value:
            return integer_value

        return rounded

    @staticmethod
    async def user_tariff_info(user_id: int) -> UserTariffInfoInterface:
        tariff_info: UserTariffInfoInterface = await tariff_repository.user_tariff_info(user_id)
        if tariff_info is None:
            user_base_currency_code = await tariff_repository.get_currency_code_for_user(user_id)
            tariff_info = {
                'channels_count': 0,
                'currency_code': user_base_currency_code,
                'price': 0,
                'balance': 0,
                'end_date': None,
                'user_id': user_id,
                'tariff_id': 0,
                'trial_was_activated': False
            }

        return tariff_info

    # @staticmethod
    # def tariffs() -> list[TariffInterface]:
    #     return tariff_repository.tariffs()

    @staticmethod
    async def tariffs_info(user_id: int) -> list[TariffInfoInterface]:
        return await tariff_repository.tariffs_info(user_id)

    # @staticmethod
    # async def find(tariff_id: int) -> TariffInfoInterface | None:
    #     return await tariff_repository.find(tariff_id)

    @staticmethod
    async def initiate(user_id: int) -> UserTariffConnectionInterface:
        current_tariff = await tariff_repository.user_subscription(user_id)
        if current_tariff is not None:
            return current_tariff

        subscription: UserTariffConnectionInterface = {
            'user_id': user_id,
            'tariff_id': 0,
            'balance': 0,
            'currency_code': await tariff_repository.currency_code_for_user(user_id),
            'end_date': None,
            'trial_was_activated': False
        }

        return await tariff_repository.update_subscription(subscription, create=True)

    @staticmethod
    async def activate_trial(user_tariff_info: UserTariffInfoInterface) -> None | UserTariffConnectionInterface:
        if user_tariff_info['trial_was_activated'] is True:
            return None

        if user_tariff_info['balance'] != 0 or user_tariff_info['end_date'] is not None \
                or user_tariff_info['tariff_id'] != 0:
            subscription: UserTariffConnectionInterface = {
                'user_id': user_tariff_info['user_id'],
                'trial_was_activated': True
            }
            return await tariff_repository.update_subscription(subscription)

        trial_tariff = await Tariff.tariff_info(constants.tariff_free_trail_id, user_tariff_info['user_id'])

        subscription: UserTariffConnectionInterface = {
            'user_id': user_tariff_info['user_id'],
            'tariff_id': trial_tariff['id'],
            'balance': 0,
            'currency_code': trial_tariff['currency_code'],
            'end_date':
                datetime.datetime.now()
                + datetime.timedelta(days=constants.tariff_free_trail_days),
            'trial_was_activated': True
        }

        return await tariff_repository.update_subscription(subscription)

    @staticmethod
    async def change(user_id: int, chosen_tariff_id: int, force=False) \
            -> UserTariffConnectionInterface | ErrorDictInterface:
        user_subscription = await Tariff.user_tariff_info(user_id)
        if user_subscription['tariff_id'] == chosen_tariff_id:
            return {'error': 'already_chosen'}

        chosen_tariff = await Tariff.tariff_info(chosen_tariff_id, user_id)
        user_tariff = await Tariff.tariff_info(user_subscription['tariff_id'], user_id)

        # How many the user must pay
        if force is False:
            if user_subscription['tariff_id'] == 0:
                change_sum = chosen_tariff['price']
                new_subscription_end_date = datetime.datetime.now() + datetime.timedelta(
                    days=constants.tariff_duration_days)

            else:
                # Do not take into account the current day, since part of it has passed, charge again
                if user_subscription['end_date'] is None:
                    days_left = constants.tariff_duration_days
                else:
                    days_left = (user_subscription['end_date'] - datetime.datetime.now()).days

                if days_left > 0:
                    # Change sum is positive when chosen tariff is more expensive
                    change_sum = int(
                        (days_left / constants.tariff_duration_days) * chosen_tariff['price']
                        - ((days_left - 1) / constants.tariff_duration_days) * user_tariff['price']
                    )
                else:
                    change_sum = chosen_tariff['price']

                new_subscription_end_date = (None if chosen_tariff['id'] == 0 else user_subscription['end_date'])

            # Can the user pay for the best tariff?
            if change_sum > 0 and user_subscription['balance'] < change_sum:
                return {'error': 'not_enough_balance'}

        else:  # if force is True:
            change_sum = 0
            if user_subscription['tariff_id'] == 0:
                new_subscription_end_date = datetime.datetime.now()
            else:
                new_subscription_end_date = (None if chosen_tariff['id'] == 0 else user_subscription['end_date'])

        new_subscription: UserTariffConnectionInterface = {
            'user_id': user_id,
            'tariff_id': chosen_tariff['id'],
            'balance': user_subscription['balance'] - change_sum,
            'currency_code': user_subscription['currency_code'],
            'end_date': new_subscription_end_date,
        }

        return await tariff_repository.update_subscription(new_subscription)

    @staticmethod
    async def add_amount(user_id: int, amount: int) -> int:
        return await tariff_repository.increase_amount(user_id, amount)

    @staticmethod
    async def prolong(user_id: int, days: int) -> datetime:
        return await tariff_repository.move_end_date(user_id, days)

    @staticmethod
    async def chats_number_satisfactory(user_chat_id: int, strong: bool = True) -> bool:
        return await tariff_repository.chats_number_satisfactory(str(user_chat_id), strong)

    @staticmethod
    async def process_all_subscription_validity() -> Generator[ProcessSubscriptionInterface, None, None]:
        user: ProcessSubscriptionInterface

        async for user in tariff_repository.process_subscriptions():
            yield user

    @staticmethod
    async def users_with_remaining_days(notify_about_days: int) -> Generator[UserInterface, None, None]:
        user: UserInterface

        async for user in tariff_repository.users_with_remaining_days(notify_about_days):
            yield user

    @staticmethod
    async def currency_code_for_user(user_id: int):
        return await tariff_repository.currency_code_for_user(user_id)

    @staticmethod
    async def add_payment_history(payment_history: PaymentHistoryInterface) -> PaymentHistoryInterface:
        return await tariff_repository.add_payment_history(payment_history)
