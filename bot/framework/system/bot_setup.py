from aiogram import Bot, Dispatcher

from pkg.config.config import environment

bot = Bot(environment['TELEGRAM_BOT_TOKEN'])
dispatcher = Dispatcher()
