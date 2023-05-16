import asyncio
import datetime

from framework.controller.message_tools import message_sender
from pkg.service.tariff import Tariff
from pkg.service.user_storage import UserStorage
from pkg.system.logger import logger
from pkg.template.tariff import auto_update


async def subscription_handler():
    while True:
        # await asyncio.sleep(5)
        logger.info("Subscription Handler:", datetime.datetime.now())

        # Prolong or disable users
        await subscription_handler_action()

        # Notify about days left
        await subscription_handler_notifier()

        # Wait to the next hour
        delta = datetime.timedelta(hours=1)
        now = datetime.datetime.now()
        next_hour = (now + delta).replace(microsecond=0, second=0, minute=0)
        wait_seconds = (next_hour - now).seconds
        logger.info("Subscription Handler:", f"Sleeping for {wait_seconds}")
        await asyncio.sleep(1)  # Ensure unique per interval
        await asyncio.sleep(wait_seconds)


async def subscription_handler_action():
    logger.info("Subscription Handler: performing action part")
    for process_subscription_data in Tariff.process_all_subscription_validity():
        logger.info("Subscription Handler:", "Processing ", process_subscription_data)

        try:
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

        except Exception as e:
            logger.error(e, "Subscription Handler")


async def subscription_handler_notifier():
    notify_about_days = 1
    logger.info(f"Subscription Handler, performing notify, days left: {notify_about_days}")
    for user in Tariff.users_with_remaining_days(notify_about_days):
        logger.info("Subscription Handler:", f"Notifying {user['id']}")

        try:
            await message_sender(int(user['service_id']), resending=True, message_structures=[{
                'type': 'text',
                'text': auto_update.remaining_days_left_message(
                    user['id'], user['language_code'], notify_about_days),
                'parse_mode': 'HTML'
            }])
            UserStorage.set_resend(int(user['service_id']))
        except Exception as e:
            logger.error(e, "Subscription Handler")
