import os

# import config

from pkg.config.routes import init_routes

# from db.adapter import database
# from utils import get_username_from_command

environment = {
    "TELEGRAM_BOT_TOKEN": os.environ['TELEGRAM_BOT_TOKEN']
}

executor, dp = init_routes(environment)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=False)
