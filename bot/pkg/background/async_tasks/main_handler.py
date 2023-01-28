import asyncio

from aiogram import Dispatcher

from pkg.background.async_tasks.subscription_handler import subscription_handler


async def on_bot_startup(dispatcher: Dispatcher) -> None:
    asyncio.create_task(subscription_handler(dispatcher))

