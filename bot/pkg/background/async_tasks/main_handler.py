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
        await MessageSender.notify_admins('The tasks have been started')
    logger.info("The tasks have been started")

    # The loop is starts by aiogram
    # loop.run_forever()


async def on_bot_startup(bot: Bot) -> None:
    if environment['ENVIRONMENT'] != 'development':
        await MessageSender.notify_admins('The bot has been started')
    logger.info("The bot has been started")
