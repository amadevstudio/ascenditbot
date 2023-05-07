import asyncio
import datetime

from aiogram import Bot

from framework.controller.message_tools import message_sender
from pkg.service.tariff import Tariff
from pkg.service.user_storage import UserStorage
from pkg.system.logger import logger
from pkg.template.tariff import auto_update


async def subscription_handler(bot: Bot):
    while True:
        # await asyncio.sleep(5)
        logger.log('--- Subscription Handler')
        logger.log(datetime.datetime.now())

        # Prolong or disable users
        for process_subscription_data in Tariff.process_all_subscription_validity():
            logger.log("Subscription processing", process_subscription_data)
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
                await message_sender(int(user['service_id']), resending=True, message_structures=message_structures)
                UserStorage.set_resend(int(user['service_id']))

        # Notify about days left
        notify_about_days = 1
        for user in Tariff.users_with_remaining_days(notify_about_days):
            logger.log(f"NOTIFYING USER {user}")
            await message_sender(int(user['service_id']), resending=True, message_structures=[{
                'type': 'text',
                'text': auto_update.remaining_days_left_message(
                    user['id'], user['language_code'], notify_about_days),
                'parse_mode': 'HTML'
            }])
            UserStorage.set_resend(int(user['service_id']))

        logger.log('===\n')

        # Wait to the next hour
        delta = datetime.timedelta(hours=1)
        now = datetime.datetime.now()
        next_hour = (now + delta).replace(microsecond=0, second=0, minute=0)
        wait_seconds = (next_hour - now).seconds
        await asyncio.sleep(wait_seconds)
        await asyncio.sleep(1)  # Ensure unique per interval

# TODO: notify about 1 day left, maybe using redis to cache notified today users
