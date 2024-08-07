import typing

from framework.controller.message_tools import chat_id_sender
from lib.language import localization
from lib.payment.payment import CallableInterface, PaymentProcessor
from lib.payment.services import robokassa
from lib.telegram.aiogram.message_master import InlineButtonData, reply_markup_type
from pkg.config.config import environment
from framework.system.bot_setup import bot
from pkg.service.service import Service
from pkg.service.tariff import Tariff
from pkg.service.user import User
from pkg.system.logger import logger
from pkg.template.tariff.common import build_subscription_info
from project import constants
from project.types import UserInterface


class BalanceHandler(Service):
    BOT = bot

    # Usage example
    # import main
    # import asyncio
    # from pkg.service.payment import BalanceHandler
    # from pkg.config.config import environment
    # database_configuration = {"host": "db","database": environment["POSTGRES_DB"],"user": environment["POSTGRES_USER"],"password": environment["POSTGRES_PASSWORD"]}
    # from pkg.repository.database_connection import Database
    # asyncio.run(Database(max_connections=1, min_alive_connections=1).connect(database_configuration))
    # asyncio.run(BalanceHandler.funding({'amount': 50000, 'currency': 'rub', 'user_id': 12, 'service': 'robokassa'}))
    @classmethod
    async def funding(cls, result: CallableInterface):
        user = await User.get_by_id(result['user_id'])
        if user is None:
            logger.warning(f"The user with id {result['user_id']} was not found.")
            return

        language_code = user['language_code']

        markup: reply_markup_type = [[{
            'text': localization.get_message(['buttons', 'menu'], language_code),
            'callback_data': {'tp': 'menu'}}]]

        # An error occurred
        if 'error' in result:
            await chat_id_sender(int(user['service_id']), message_structures=[{
                'type': 'text',
                'text': localization.get_message(
                    ['subscription', 'fund', 'errors', 'wrong_signature'], language_code),
                'parse_mode': 'HTML',
                'reply_markup': markup
            }])
            logger.warning('Error wrong_signature', result, user, result['error'])
            return

        user_tariff_info = await Tariff.user_tariff_info(user['id'])

        # Wrong currency
        if user_tariff_info is None or user_tariff_info['currency_code'] != result['currency']:
            await chat_id_sender(int(user['service_id']), message_structures=[{
                'type': 'text',
                'text': localization.get_message(
                    ['subscription', 'fund', 'errors', 'wrong_currency_income'], language_code),
                'parse_mode': 'HTML',
                'reply_markup': markup
            }])
            logger.warning('Error wrong_currency_income', result, user, user_tariff_info)
            return

        # Funding
        new_balance = await Tariff.add_amount(user['id'], result['amount'])
        await Tariff.add_payment_history({
            'user_id': user['id'],
            'payment_service': result['service'],
            'amount': result['amount'],
            'currency_code': result['currency']})

        new_user_tariff_info = await Tariff.user_tariff_info(user['id'])
        if new_user_tariff_info['balance'] != new_balance:
            new_user_tariff_info = {**new_user_tariff_info, 'balance': new_balance}

        # Notify user
        success_message = localization.get_message(['subscription', 'fund', 'success_payment'], language_code)
        success_message += "\n\n" + localization.get_message(['tariffs', 'current'], language_code) \
                           + "\n" + build_subscription_info(new_user_tariff_info, language_code)

        await chat_id_sender(int(user['service_id']), message_structures=[{
            'type': 'text',
            'text': success_message,
            'parse_mode': 'HTML',
            'reply_markup': markup
        }])

        # Notify admins
        telegram_admin_group_id = environment.get('TELEGRAM_ADMIN_GROUP_ID', None)
        if telegram_admin_group_id is not None:
            await chat_id_sender(int(telegram_admin_group_id), message_structures=[{
                'type': 'text',
                'text':
                    f"New payment from user {user['id']}, email: {user['email']}, amount {result['amount']},"
                    f" new balance {new_balance} (bd: {new_user_tariff_info['balance']})"
            }])

        # Check referrer
        await cls.reward_referrer(user, result['amount'])

    @classmethod
    async def reward_referrer(cls, referral: UserInterface, amount: int):
        if referral['ref_id'] is None:
            return

        referrer = await User.get_by_id(referral['ref_id'])
        if referrer is None:
            return

        referrer_tariff_info = await Tariff.user_tariff_info(referrer['id'])

        # Promote tariff if disabled
        if referrer_tariff_info['tariff_id'] == 0:
            await Tariff.change(referrer['id'], constants.tariff_free_trail_id, force=True)
            referrer_tariff_info = await Tariff.user_tariff_info(referrer['id'])

        tariff_as_referral = await Tariff.tariff_info(
            typing.cast(int, referrer_tariff_info['tariff_id']), referral['id'])

        # Reward as part of incoming sum
        reward_days = int(amount * constants.tariff_duration_days / tariff_as_referral['price'])
        if reward_days > constants.tariff_duration_days:
            reward_days = constants.tariff_duration_days
        reward_days = int(reward_days * constants.referred_days_part)

        if reward_days == 0:
            return

        new_end_date = await Tariff.prolong(referrer['id'], reward_days)

        new_user_tariff_info = await Tariff.user_tariff_info(referrer['id'])
        if new_user_tariff_info['end_date'] != new_end_date:
            new_user_tariff_info = {**new_user_tariff_info, 'end_date': new_end_date}

        # Notify referrer
        success_message = localization.get_message(
            ['subscription', 'fund', 'from_referral', 'prolonged'], referrer['language_code'])
        success_message += "\n\n" + localization.get_message(['tariffs', 'current'], referrer['language_code']) \
                           + "\n" + build_subscription_info(new_user_tariff_info, referrer['language_code'])

        await chat_id_sender(int(referrer['service_id']), message_structures=[{
            'type': 'text',
            'text': success_message,
            'parse_mode': 'HTML',
            'reply_markup': [[{
            'text': localization.get_message(['buttons', 'menu'], referrer['language_code']),
            'callback_data': {'tp': 'menu'}}]]
        }])


payment_processors: dict[str, PaymentProcessor] = {
    'robokassa.ru': robokassa.RobokassaPaymentProcessor({
        'login': environment['ROBOKASSA_LOGIN'],
        'password_1': environment['ROBOKASSA_PAYMENT_P1'],
        'password_2': environment['ROBOKASSA_PAYMENT_P2'],
        'password_1_test': environment['ROBOKASSA_PAYMENT_P1_TEST'],
        'password_2_test': environment['ROBOKASSA_PAYMENT_P2_TEST'],
        'test': False if environment['ENVIRONMENT'] == 'production' else True
    }, BalanceHandler.funding, logger=logger)
}


class Payment(Service):
    # @staticmethod
    # def is_test(text: str) -> [float, str]:
    #     if len(text) > 0 and text[0] == 't':
    #         return True, text[1:]
    #     else:
    #         return False, text

    @staticmethod
    def get_fund_service() -> str:
        return 'robokassa.ru'

    @staticmethod
    def generate_payment_link(amount: float, user: UserInterface, currency_code: str, fund_service: str) \
            -> str | robokassa.ErrorDictInterface:
        return payment_processors[fund_service].generate_payment_link(
            amount, user['id'], currency_code, user['language_code'],
            test=user['is_admin'])
