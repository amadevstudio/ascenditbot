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

# database_connection

executor, dp = init_routes(environment)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=False)
