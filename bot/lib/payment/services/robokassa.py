import hashlib
from typing import TypedDict

from lib.payment.payment import PaymentProcessor, ErrorDictInterface


class PackageParams(TypedDict, total=False):
    out_summ: str  # '930.73' Always in rubbles
    OutSum: str  # '930.73' Always in rubbles
    inv_id: str  # '3'
    InvId: str  # '3'
    crc: str  # 'BBAFFB...'
    SignatureValue: str  # 'BBAFFB...'
    PaymentMethod: str  # 'Qiwi'
    IncSum: str  # '970.73' Always in rubbles
    IncCurrLabel: str  # Payment currency, 'Qiwi40PS'
    IsTest: str  # '1'
    EMail: str  # ''
    Fee: str  # '0.0'
    Shp_Currency: str  # 'usd' Currency set by the project
    Shp_Sum: str  # '14.0'
    Shp_UserId: str  # '3'


class RobokassaPaymentProcessor(PaymentProcessor):
    AVAILABLE_CURRENCIES = ['rub', 'usd', 'eur', 'kzt']

    def validate_package(self, package: dict, service: str) -> bool:
        return service == 'robokassa'

    async def process_package(self, package_params: PackageParams) -> str:
        out_sum = package_params.get('OutSum', '')
        inv_id = package_params.get('InvId', '')
        currency = package_params.get('Shp_Currency', '')
        summ = package_params.get('Shp_Sum', '')
        user_id = package_params.get('Shp_UserId', '')

        payment_password = self.credentials['password_2'] if package_params.get('IsTest') != '1' \
            else self.credentials['password_2_test']

        secure_seed = f"{out_sum}" \
                      f":{inv_id}" \
                      f":{payment_password}" \
                      f":Shp_Currency={currency}" \
                      f":Shp_Sum={summ}" \
                      f":Shp_UserId={user_id}"

        signature = hashlib.md5(secure_seed.encode()).hexdigest().upper()

        result = (signature == package_params.get('SignatureValue', ''))

        result_summ = int(float(summ) * 100)

        if result:
            result_text = f"OK{inv_id}"
            await self.incoming_payment_callback({
                'amount': result_summ, 'currency': currency, 'user_id': int(user_id), 'service': 'robokassa'})
        else:
            result_text = 'BAD'
            await self.incoming_payment_callback({'error': 'wrong_signature', 'user_id': int(user_id)})
            self.log('wrong_signature', package_params, signature)

        return result_text

    def generate_payment_link(
            self, summ: int, user_id: int, currency: str, culture: str = None, test: bool = False
    ) -> str | ErrorDictInterface:
        inv_id = 0  # max 2^31 - 1

        if currency not in self.AVAILABLE_CURRENCIES:
            return {'error': 'currency_not_available'}

        is_test = self.credentials['test'] or test

        payment_password = (self.credentials['password_1'] if not is_test else self.credentials['password_1_test'])

        use_currency = currency != 'rub'

        secure_seed = f"{self.credentials['login']}" \
                      f":{summ}" \
                      f":{inv_id}" \
                      + (f":{currency}" if use_currency else '') \
                      + f":{payment_password}" \
                        f":Shp_Currency={currency}" \
                        f":Shp_Sum={summ}" \
                        f":Shp_UserId={user_id}"
        signature = hashlib.md5(secure_seed.encode()).hexdigest()

        return f"https://auth.robokassa.ru/Merchant/Index.aspx?" \
               f"MerchantLogin={self.credentials['login']}" \
               f"&InvId={inv_id}" \
               f"&Culture={culture}" \
               f"&Encoding=utf-8" \
               f"&Description={user_id}" \
               f"&OutSum={summ}" \
            + (f"&OutSumCurrency={currency}" if use_currency else '') \
            + f"&Shp_Currency={currency}" \
              f"&Shp_Sum={summ}" \
              f"&Shp_UserId={user_id}" \
              f"&SignatureValue={signature}" \
            + ("&IsTest=1" if is_test else "")
