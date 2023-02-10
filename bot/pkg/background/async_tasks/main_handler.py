import asyncio

from aiogram import Dispatcher

from pkg.background.async_tasks.subscription_handler import subscription_handler
from pkg.system.logger import logger


async def on_bot_startup(dispatcher: Dispatcher) -> None:
    logger.log("The bot is started")
    asyncio.create_task(subscription_handler(dispatcher))

