from lib.payment.payment import CallableInterface, PaymentProcessor, PaymentServer
from lib.payment.services import robokassa
from pkg.config.config import environment
from pkg.service.service import Service
from project.types import UserInterface


class IncomingPayment(Service):
    @staticmethod
    def incoming_subscription(result: CallableInterface):
        # TODO
        pass


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
