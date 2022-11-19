from aiogram import Bot, Dispatcher, executor, types

import os
os.chdir('/')

import config

from pkg.controller.routes import init_routes

# from db.adapter import database

# from utils import get_username_from_command

bot = Bot(token=os.environ['TELEGRAM_BOT_TOKEN'])
dp = Dispatcher(bot)


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=False)
