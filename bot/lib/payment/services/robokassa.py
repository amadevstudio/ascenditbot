from lib.payment.payment import PaymentProcessor


class RobokassaPaymentProcessor(PaymentProcessor):
    def validate_package(self, package: dict) -> bool:
        # TODO
        return True

    def process_package(self, package: dict):
        # TODO
        result = True
        amount = 100

        if result:
            self.callback({'amount': amount})
        else:
            self.callback({'error': 'error'})

    def generate_payment_link(self, amount) -> str:
        return f"zxc.com/?amount={amount}"
