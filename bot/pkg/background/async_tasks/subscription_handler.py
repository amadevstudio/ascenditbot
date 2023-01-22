import asyncio
import datetime

from aiogram import Dispatcher

from framework.controller.message_tools import chat_id_sender
from pkg.service.tariff import Tariff
from pkg.template.tariff import auto_update


async def subscription_handler(dispatcher: Dispatcher):
    bot = dispatcher.bot

    while True:
        # Wait to the next hour
        delta = datetime.timedelta(hours=1)
        now = datetime.datetime.now()
        next_hour = (now + delta).replace(microsecond=0, second=0, minute=0)
        wait_seconds = (next_hour - now).seconds
        await asyncio.sleep(wait_seconds)
        await asyncio.sleep(1)  # Ensure unique per interval

        # await asyncio.sleep(5)
        # print('---')
        # print(datetime.datetime.now())

        for process_subscription_data in Tariff.process_all_subscription_validity():
            print(process_subscription_data)
            user = process_subscription_data['user']

            if process_subscription_data['action'] == 'prolonged':
                message_text = auto_update.prolonged_message(
                    user['id'], user['language_code'], process_subscription_data['prolongable'])

            elif process_subscription_data['action'] == 'disabled':
                message_text = auto_update.disabled_message(
                    user['id'], user['language_code'])

            else:
                message_text = None

            if message_text is not None:
                message_structures = [{
                    'type': 'text',
                    'text': message_text,
                    'parse_mode': 'HTML'
                }]
                await chat_id_sender(bot, int(user['service_id']), message_structures=message_structures)

        # print('===\n')

# TODO: notify about 1 day left
