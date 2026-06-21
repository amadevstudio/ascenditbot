from aiogram import F, Router

from pkg.service.telegram_stars import TelegramStarsPayment


def payment_router():
    router = Router()

    router.pre_checkout_query.register(TelegramStarsPayment.pre_checkout)
    router.message.register(TelegramStarsPayment.successful_payment, F.successful_payment)

    return router
