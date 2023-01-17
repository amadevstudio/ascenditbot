import asyncio
import datetime

from pkg.service.tariff import Tariff


async def subscription_handler():
    while True:
        # Wait to the next hour
        delta = datetime.timedelta(hours=1)
        now = datetime.datetime.now()
        next_hour = (now + delta).replace(microsecond=0, second=0, minute=0)
        wait_seconds = (next_hour - now).seconds
        # await asyncio.sleep(wait_seconds)
        await asyncio.sleep(1)  # Ensure unique per interval

        Tariff.process_all_subscription_validity()
