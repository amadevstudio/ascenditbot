import asyncio
import datetime

from framework.controller.message_tools import message_sender
from lib.language import localization
from pkg.service.channel_bonus import ChannelBonus
from pkg.service.member_alerts import MemberAlerts
from pkg.service.tariff import Tariff
from pkg.service.user_storage import UserStorage
from pkg.system.logger import logger
from pkg.template.tariff import auto_update


async def subscription_handler():
    while True:
        await subscription_handler_round()

        # Wait to the next hour
        delta = datetime.timedelta(hours=1)
        now = datetime.datetime.now()
        next_hour = (now + delta).replace(microsecond=0, second=0, minute=0)
        wait_seconds = (next_hour - now).seconds
        logger.info("Subscription Handler:", f"Sleeping for {wait_seconds}")
        await asyncio.sleep(1)  # Ensure unique per interval
        await asyncio.sleep(wait_seconds)


async def subscription_handler_round():
    """One hourly round. A failure (the database unreachable for a moment) must not end the task: it did twice
    in 2026 and subscriptions were neither prolonged nor disabled until the bot restarted."""
    logger.info("Subscription Handler:", datetime.datetime.now())
    try:
        # Prolong or disable users
        await subscription_handler_action()

        # Notify about days left
        await subscription_handler_notifier()

        # Timed whitelist access: remind the managers a day before it ends, tell them when it has
        await MemberAlerts.expiry_round()

        # Took the bonus for subscribing: still subscribed? (each taker once a day)
        await ChannelBonus.recheck_round(notify_bonus_lost)
    except Exception as e:
        logger.error(e, "Subscription Handler: the round failed, the next one is in an hour")


async def subscription_handler_action():
    logger.info("Subscription Handler: action part")
    async for process_subscription_data in Tariff.process_all_subscription_validity():
        logger.info("Subscription Handler:", "Processing ", process_subscription_data)

        try:
            user = process_subscription_data['user']

            if process_subscription_data['action'] == 'prolonged':
                message_text = await auto_update.prolonged_message(
                    user['id'], user['language_code'], process_subscription_data['prolongable'])

            elif process_subscription_data['action'] == 'disabled':
                message_text = await auto_update.disabled_message(
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
    logger.info(f"Subscription Handler, notify part with days: {notify_about_days}")
    async for user in Tariff.users_with_remaining_days(notify_about_days):
        logger.info("Subscription Handler:", f"Notifying {user['id']}")

        try:
            await message_sender(int(user['service_id']), resending=True, message_structures=[{
                'type': 'text',
                'text': await auto_update.remaining_days_left_message(
                    user['id'], user['language_code'], notify_about_days),
                'parse_mode': 'HTML'
            }])
            UserStorage.set_resend(int(user['service_id']))
        except Exception as e:
            logger.error(e, "Subscription Handler")


async def notify_bonus_lost(claim: dict, channels: list[dict]):
    """Unsubscribed after taking the bonus: the free group waits, and how to get it back."""
    from pkg.controller.user_controllers.channel_bonus_controller import channel_buttons, channel_names
    try:
        await message_sender(int(claim['service_id']), resending=True, message_structures=[{
            'type': 'text', 'parse_mode': 'HTML', 'disable_web_page_preview': True,
            'text': localization.get_message(['bonus', 'lost_notice'], claim['language_code'],
                                             channels=channel_names(channels)),
            'reply_markup': channel_buttons(channels)}])
        UserStorage.set_resend(int(claim['service_id']))
    except Exception as e:
        logger.warning('Channel bonus: cannot tell the user', claim['user_id'], e)
