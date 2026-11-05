import asyncio

from aiogram import Bot

from pkg.config.config import environment
from pkg.service.bot_commands import set_bot_commands
from pkg.service.message_sender import MessageSender
from pkg.background.async_tasks.subscription_handler import subscription_handler
from pkg.service.access_payments import poll_forever
from pkg.system.logger import logger


async def before_bot_startup() -> None:
    loop = asyncio.get_event_loop()

    loop.create_task(subscription_handler())
    # Invoices of payment providers (CryptoBot) the members of groups are paying
    loop.create_task(poll_forever())

    if environment['ENVIRONMENT'] != 'development':
        await MessageSender.notify_admins('The tasks have been started')
    logger.info("The tasks have been started")

    # The loop is starts by aiogram
    # loop.run_forever()


async def on_bot_startup(bot: Bot) -> None:
    await set_bot_commands(bot)
    if environment['ENVIRONMENT'] != 'development':
        await MessageSender.notify_admins('The bot has been started')
    logger.info("The bot has been started")
