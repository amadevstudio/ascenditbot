import asyncio
import datetime

from framework.controller.message_tools import chat_id_sender
from pkg.service.tariff import Tariff


async def subscription_handler():
    global message_text
    while True:
        # Wait to the next hour
        delta = datetime.timedelta(hours=1)
        now = datetime.datetime.now()
        next_hour = (now + delta).replace(microsecond=0, second=0, minute=0)
        wait_seconds = (next_hour - now).seconds
        await asyncio.sleep(wait_seconds)
        await asyncio.sleep(1)  # Ensure unique per interval

        await asyncio.sleep(5)
        print('---')
        print(datetime.datetime.now())
        print('===\n')

        for process_subscription_data in Tariff.process_all_subscription_validity():
            user = process_subscription_data['user']
            message_text: str

            if process_subscription_data['action'] == 'prolonged':
                message_text = "prolonged!"

                if process_subscription_data['prolongable'] is False:
                    message_text += "can't prolong in future!"

            elif process_subscription_data['action'] == 'disabled':
                message_text = "tariff disabled! fill and re-subscribe!"

            message_structures = [{
                'type': 'text',
                'text': message_text
            }]
            await chat_id_sender(message_text, message_structures=message_structures)

