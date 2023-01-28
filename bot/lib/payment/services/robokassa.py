import hashlib

from lib.payment.payment import PaymentProcessor, ErrorDictInterface


class RobokassaPaymentProcessor(PaymentProcessor):
    AVAILABLE_CURRENCIES = ['rub', 'usd', 'eur', 'kzt']

    def validate_package(self, package: dict) -> bool:
        print("Incoming package")
        print(package)
        return True

    def process_package(self, package: dict) -> str:
        # TODO validate
        result_text = '...'  # TODO

        result = True
        amount = 100

        if result:
            self.incoming_payment_callback({'amount': amount})
        else:
            self.incoming_payment_callback({'error': 'error'})

        return result_text

    def generate_payment_link(
            self, sum: int, user_id: int, currency: str, culture: str = None) -> str | ErrorDictInterface:
        inv_id = 0  # max 2^31 - 1

        if currency not in self.AVAILABLE_CURRENCIES:
            return {'error': 'currency_not_available'}

        # payment_password = (self.credentials['password_1'] if not test else self.credentials['password_1_test'])
        payment_password = self.credentials['password_1']

        is_test = self.credentials['test']

        use_currency = currency != 'rub'

        secure_seed = f"{self.credentials['login']}" \
                      f":{sum}" \
                      f":{inv_id}" \
                      + (f":{currency}" if use_currency else '') \
                      + f":{payment_password}" \
                      f":Shp_Currency={currency}" \
                      f":Shp_Sum={sum}" \
                      f":Shp_UserId={user_id}"
        signature = hashlib.md5(secure_seed.encode()).hexdigest()

        return f"https://auth.robokassa.ru/Merchant/Index.aspx?" \
               f"MerchantLogin={self.credentials['login']}&" \
               f"InvId={inv_id}&" \
               f"Culture={culture}&" \
               f"Encoding=utf-8&" \
               f"Description={user_id}&" \
               f"OutSum={sum}&" \
               + (f"OutSumCurrency={currency}&" if use_currency else '') \
               + f"Shp_Currency={currency}&" \
               f"Shp_Sum={sum}&" \
               f"Shp_UserId={user_id}&" \
               f"SignatureValue={signature}&" \
            + ("&IsTest=1" if is_test else "")
