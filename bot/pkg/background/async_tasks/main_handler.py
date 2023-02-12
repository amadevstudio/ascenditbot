import asyncio

from aiogram import Dispatcher

from pkg.service.message_sender import MessageSender
from pkg.background.async_tasks.subscription_handler import subscription_handler
from pkg.system.logger import logger


async def on_bot_startup(dispatcher: Dispatcher) -> None:
    await MessageSender.notify_admins('The bot is started')
    logger.log("The bot is started")

    asyncio.create_task(subscription_handler(dispatcher))

