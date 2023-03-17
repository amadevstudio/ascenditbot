import asyncio

from lib.language import localization
from lib.payment.payment import PaymentServer
from lib.telegram.aiogram.navigation_builder import NavigationBuilder
from pkg.background.async_tasks.main_handler import on_bot_startup, before_bot_startup
from pkg.config.config import environment
from pkg.controller.bot_setup import bot, dispatcher

from pkg.controller.router import init_routes

from pkg.repository.database_connection import Database
from pkg.repository.storage_connection import Storage
from pkg.service.payment import payment_processors

# from db.adapter import database
# from utils import get_username_from_command

storage_configuration = {
    "host": "storage",
    "port": 6379,
    "password": environment["REDIS_PASSWORD"]
}
storage_connection = Storage().connect(storage_configuration)

database_configuration = {
    "host": "db",
    "database": environment["POSTGRES_DB"],
    "user": environment["POSTGRES_USER"],
    "password": environment["POSTGRES_PASSWORD"]
}
database_connection = Database().connect(database_configuration)

NavigationBuilder(localization.get_message, ["navigation_builder"])

dp = dispatcher
init_routes(dp)


async def run():
    server = PaymentServer(3000, list(payment_processors.values()))

    await bot.delete_webhook(drop_pending_updates=False)
    await before_bot_startup(bot)
    await dp.start_polling(bot)  # , on_startup=on_bot_startup)
    await on_bot_startup(bot)


if __name__ == "__main__":
    asyncio.run(run())
