from lib.language import localization
from lib.payment.payment import CallableInterface, PaymentProcessor, PaymentServer
from lib.payment.services import robokassa
from pkg.config.config import environment
from pkg.controller import bot
from pkg.service.service import Service
from pkg.service.tariff import Tariff
from pkg.service.user import User
from pkg.system.logger import logger
from pkg.template.tariff.common import build_subscription_info
from project.types import UserInterface


class IncomingPayment(Service):
    BOT = bot.bot

    @staticmethod
    def incoming_subscription(result: CallableInterface):
        user: UserInterface = User.get_by_id(result['user_id'])
        language_code = user['language_code']

        if 'error' in result:
            IncomingPayment.BOT.send_message(user['service_id'], localization.get_message(
                ['subscription', 'fund', 'errors', 'wrong_signature'], language_code))
            logger.warn('Error wrong_signature', result, user, result['error'])
            return

        user_tariff_info = Tariff.user_tariff_info(user['id'])

        if user_tariff_info is None or user_tariff_info != result['currency']:
            IncomingPayment.BOT.send_message(user['service_id'], localization.get_message(
                ['subscription', 'fund', 'errors', 'wrong_currency_income'], language_code))
            logger.warn('Error wrong_currency_income', result, user, user_tariff_info)
            return

        new_balance = Tariff.add_amount(user['id'], result['amount'])

        new_user_tariff_info = Tariff.user_tariff_info(user['id'])

        if new_user_tariff_info['balance'] != new_balance:
            new_user_tariff_info = {**new_user_tariff_info, 'balance': new_balance}

        success_message = localization.get_message(['subscription', 'fund', 'success_payment'], language_code)
        success_message += "\n\n" + localization.get_message(['tariffs', 'current'], language_code) \
                           + "\n" + build_subscription_info(new_user_tariff_info, language_code)

        IncomingPayment.BOT.send_message(user['service_id'], success_message)


payment_processors: dict[str, PaymentProcessor] = {
    'robokassa.ru': robokassa.RobokassaPaymentProcessor({
        'login': environment['ROBOKASSA_LOGIN'],
        'password_1': environment['ROBOKASSA_PAYMENT_P1'],
        'test': False if environment['ENVIRONMENT'] == 'production' else True
    }, IncomingPayment.incoming_subscription)
}


server = PaymentServer(3000, list(payment_processors.values()))


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
            amount, user['id'], currency_code, user['language_code'])
