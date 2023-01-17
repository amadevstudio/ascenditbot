from lib.language import localization
from lib.telegram.aiogram.navigation_builder import NavigationBuilder
from pkg.background.async_tasks.main_handler import on_bot_startup
from pkg.config.config import environment

from pkg.controller.router import init_routes

from pkg.repository.database_connection import Database
from pkg.repository.storage_connection import Storage

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

executor, dp = init_routes(environment)


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=False, on_startup=on_bot_startup)
