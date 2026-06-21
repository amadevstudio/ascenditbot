import uuid
from typing import TypedDict

from aiogram.types import LabeledPrice

from framework.system import telegram_types
from framework.system.bot_setup import bot
from lib.language import localization
from pkg.service.payment import BalanceHandler
from pkg.service.tariff import Tariff
from pkg.service.user import User
from pkg.system.logger import logger


class StarsPayload(TypedDict):
    kind: str
    currency_code: str
    user_id: int
    amount: int
    nonce: str


class TelegramStarsPayment:
    CURRENCY_CODE = 'xtr'
    TELEGRAM_CURRENCY_CODE = 'XTR'
    PAYMENT_SERVICE = 'telegram_stars'

    @classmethod
    def build_payload(cls, user_id: int, amount: int) -> str:
        return f"fund:{cls.CURRENCY_CODE}:{user_id}:{amount}:{uuid.uuid4().hex}"

    @classmethod
    def parse_payload(cls, payload: str) -> StarsPayload | None:
        payload_parts = payload.split(':')
        if len(payload_parts) != 5:
            return None

        kind, currency_code, user_id, amount, nonce = payload_parts
        try:
            user_id = int(user_id)
            amount = int(amount)
        except ValueError:
            return None

        return {
            'kind': kind,
            'currency_code': currency_code,
            'user_id': user_id,
            'amount': amount,
            'nonce': nonce
        }

    @classmethod
    async def send_fund_invoice(
            cls, chat_id: int, user_id: int, amount: int, language_code: str) -> None:
        payload = cls.build_payload(user_id, amount)
        title = localization.get_message(
            ['subscription', 'fund', 'telegram_stars', 'invoice_title'], language_code)
        description = localization.get_message(
            ['subscription', 'fund', 'telegram_stars', 'invoice_description'], language_code,
            amount=amount)

        await bot.send_invoice(
            chat_id=chat_id,
            title=title,
            description=description,
            payload=payload,
            provider_token='',
            currency=cls.TELEGRAM_CURRENCY_CODE,
            prices=[LabeledPrice(label=title, amount=amount)]
        )

    @classmethod
    async def validate_payment(
            cls, service_id: int, currency_code: str, amount: int, payload: str) -> tuple[bool, str | None]:
        parsed_payload = cls.parse_payload(payload)
        if parsed_payload is None:
            return False, 'wrong_payload'

        if parsed_payload['kind'] != 'fund' or parsed_payload['currency_code'] != cls.CURRENCY_CODE:
            return False, 'wrong_payload'

        if currency_code != cls.TELEGRAM_CURRENCY_CODE:
            return False, 'wrong_currency'

        if parsed_payload['amount'] != amount:
            return False, 'wrong_amount'

        user = await User.get_by_id(parsed_payload['user_id'])
        if user is None or str(user['service_id']) != str(service_id):
            return False, 'wrong_user'

        return True, None

    @classmethod
    async def pre_checkout(cls, pre_checkout_query):
        is_valid, error = await cls.validate_payment(
            pre_checkout_query.from_user.id,
            pre_checkout_query.currency,
            pre_checkout_query.total_amount,
            pre_checkout_query.invoice_payload
        )

        if is_valid:
            await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
            return

        language_code = pre_checkout_query.from_user.language_code
        error_message = localization.get_message(
            ['subscription', 'fund', 'telegram_stars', 'checkout_error'], language_code)
        await bot.answer_pre_checkout_query(
            pre_checkout_query.id,
            ok=False,
            error_message=error_message
        )
        logger.warning('Telegram Stars pre-checkout rejected', error, pre_checkout_query)

    @classmethod
    async def successful_payment(cls, message: telegram_types.Message):
        payment = message.successful_payment
        is_valid, error = await cls.validate_payment(
            message.from_user.id,
            payment.currency,
            payment.total_amount,
            payment.invoice_payload
        )
        if not is_valid:
            logger.warning('Telegram Stars successful payment rejected', error, message)
            return

        parsed_payload = cls.parse_payload(payment.invoice_payload)
        if parsed_payload is None:
            logger.warning('Telegram Stars successful payment payload parse failed', message)
            return

        await BalanceHandler.funding({
            'amount': payment.total_amount,
            'currency': cls.CURRENCY_CODE,
            'user_id': parsed_payload['user_id'],
            'service': cls.PAYMENT_SERVICE,
            'id': payment.telegram_payment_charge_id,
            'invoice_payload': payment.invoice_payload
        })
