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
        await asyncio.sleep(wait_seconds)
        await asyncio.sleep(1)  # Ensure unique per interval

        for process_subscription_data in Tariff.process_all_subscription_validity():
            user = process_subscription_data['user']
            if process_subscription_data['action'] == 'prolonged':
                message = "prolonged!"

                if process_subscription_data['prolongable'] is False:
                    message += "can't prolong in future!"

            elif process_subscription_data['action'] == 'disabled':
                message = "tariff disabled! fill and re-subscribe!"

            # Send message to user

