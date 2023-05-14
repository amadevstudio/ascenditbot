import asyncio

from aiogram import Bot

from pkg.config.config import environment
from pkg.service.message_sender import MessageSender
from pkg.background.async_tasks.subscription_handler import subscription_handler
from pkg.system.logger import logger


async def before_bot_startup() -> None:
    loop = asyncio.get_event_loop()

    loop.create_task(subscription_handler())

    if environment['ENVIRONMENT'] != 'development':
        await MessageSender.notify_admins('The tasks are started')
    logger.info("The tasks are started")

    # The loop is starts by aiogram
    # loop.run_forever()


async def on_bot_startup(bot: Bot) -> None:
    if environment['ENVIRONMENT'] != 'development':
        await MessageSender.notify_admins('The bot is started')
    logger.info("The bot is started")
