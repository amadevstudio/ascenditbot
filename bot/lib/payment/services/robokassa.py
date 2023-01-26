import hashlib
from typing import Literal

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

    def generate_payment_link(
            self, sum: int, user_id: int, currency: str, culture: str = None, test: bool = False) -> str:
        inv_id = 0  # max 2^31 - 1

        # payment_password = (self.credentials['password_1'] if not test else self.credentials['password_1_test'])
        payment_password = self.credentials['password_1']

        secure_seed = f"{self.credentials['login']}" \
                      f":{sum}" \
                      f":{inv_id}" \
                      f":{currency}" \
                      f":{payment_password}" \
                      f":Shp_Sum={sum}" \
                      f":Shp_Currency={currency}" \
                      f":Shp_UserId={user_id}"
        signature = hashlib.md5(secure_seed.encode()).hexdigest()

        return f"https://auth.robokassa.ru/Merchant/Index.aspx?" \
               f"MerchantLogin={self.credentials['login']}&" \
               f"InvId={inv_id}&" \
               f"Culture={culture}&" \
               f"Encoding=utf-8&" \
               f"Description={user_id}&" \
               f"OutSum={sum}&" \
               f"OutSumCurrency={currency}" \
               f"Shp_Sum={sum}" \
               f"Shp_Currency={currency}" \
               f"Shp_UserId={user_id}" \
               f"SignatureValue={signature}" \
            + ("&IsTest=1" if test else "")
