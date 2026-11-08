"""Bonus days for subscribing to the bot owner's channels (the admin pages list them).

Subscribed to all of them, a user gets 15 days of the paid tariff once: on top of the term they have, or from
today on the free tariff. The bonus comes with a condition, said up front: unsubscribe later and the free group
waits (tariff_repository.update_user_moderated_chats) until they subscribe again, and while the bonus days run each
channel left takes its share of what is left of them, once (subscribing again gives the free group back, not the
days). Once the bonus days are over leaving only pauses the free group: days paid for are never taken. The bot
hears of a leave at once (chat_member, bonus_channel_router) and checks each taker once a day for what it missed;
Telegram tells whether someone is in a channel only to the channel's admins, so the bot is one."""
import asyncio
import datetime
import math

from framework.system.bot_setup import bot
from pkg.repository import channel_bonus_repository, tariff_repository
from pkg.service.tariff import Tariff
from pkg.system.logger import logger
from project import constants

BONUS_DAYS = 15
# Takers checked per hourly round: each costs a getChatMember per channel
CHECKS_PER_ROUND = 30


class ChannelBonus:
    @classmethod
    async def channels(cls) -> list[dict]:
        """The listed channels, title and link fresh from Telegram: a renamed channel needs no adding again."""
        channels = [dict(channel) for channel in await channel_bonus_repository.channels()]
        await asyncio.gather(*(cls._refresh(channel) for channel in channels))
        return channels

    @classmethod
    async def _refresh(cls, channel: dict) -> None:
        """Telegram not answering (the bot lost the channel) keeps what is stored."""
        try:
            chat = await bot.get_chat(int(channel['service_id']))
        except Exception as e:
            logger.warning('Cannot refresh a bonus channel', channel['service_id'], e)
            return
        title, link = chat.title or channel['title'], cls.link(chat) or channel['link']
        if (title, link) != (channel['title'], channel['link']):
            channel.update(title=title, link=link)
            await channel_bonus_repository.update_channel(channel['service_id'], title, link)

    @staticmethod
    def link(chat) -> str | None:
        return f"https://t.me/{chat.username}" if chat.username else chat.invite_link

    @staticmethod
    async def is_subscribed(channel_service_id: str, user_service_id: int | str) -> bool | None:
        """None when Telegram did not say (the bot is no longer an admin there, the channel is gone)."""
        try:
            member = await bot.get_chat_member(int(channel_service_id), int(user_service_id))
        except Exception as e:
            logger.warning('Cannot check a subscription', channel_service_id, user_service_id, e)
            return None
        return ChannelBonus.in_channel(member)

    @staticmethod
    def in_channel(member) -> bool:
        if member.status in ('creator', 'administrator', 'member'):
            return True
        if member.status == 'restricted':
            return bool(getattr(member, 'is_member', False))
        return False

    @classmethod
    async def _not_subscribed(cls, channels: list[dict], user_service_id: int | str) -> list[dict]:
        """The channels the user is not seen in (not knowing counts as not seen: the bonus needs a yes)."""
        found = await asyncio.gather(*(cls.is_subscribed(c['service_id'], user_service_id) for c in channels))
        return [channel for channel, subscribed in zip(channels, found) if subscribed is not True]

    @staticmethod
    async def state(user_id: int) -> str | None:
        """What the menu offers: 'offer' (channels listed, bonus not taken), 'lost' (taken, then unsubscribed),
        None (nothing to say)."""
        claim = await channel_bonus_repository.claim(user_id)
        if claim is not None:
            return 'lost' if claim['lost_at'] is not None else None
        return 'offer' if await channel_bonus_repository.channels() else None

    @staticmethod
    async def claim(user_id: int) -> dict | None:
        return await channel_bonus_repository.claim(user_id)

    @classmethod
    async def take(cls, user_id: int, user_service_id: int | str) -> dict:
        """'granted' with the new end date, 'restored' (subscribed again: the free group is back), 'already', or
        {'error': 'no_channels' | 'not_subscribed', 'channels': [...]}."""
        channels = await channel_bonus_repository.channels()
        claim = await channel_bonus_repository.claim(user_id)
        if claim is not None:
            if claim['lost_at'] is None:
                return {'result': 'already'}
            channels = [c for c in channels if c['service_id'] in claim['channel_ids']]
            missing = await cls._not_subscribed(channels, user_service_id)
            if missing:
                return {'error': 'not_subscribed', 'channels': missing}
            await channel_bonus_repository.set_lost(user_id, False)
            await cls._apply_groups(user_id)
            return {'result': 'restored'}

        if not channels:
            return {'error': 'no_channels', 'channels': []}
        missing = await cls._not_subscribed(channels, user_service_id)
        if missing:
            return {'error': 'not_subscribed', 'channels': missing}
        if not await channel_bonus_repository.create_claim(user_id, [c['service_id'] for c in channels]):
            return {'result': 'already'}
        return {'result': 'granted', 'end_date': await cls._grant(user_id)}

    @staticmethod
    async def _grant(user_id: int) -> datetime.datetime:
        info = await Tariff.user_tariff_info(user_id)
        if info['tariff_id'] != Tariff.FREE_TARIFF_ID:
            # A term running (a trial or paid): the days go on top of it
            return await Tariff.prolong(user_id, BONUS_DAYS)
        end_date = datetime.datetime.now() + datetime.timedelta(days=BONUS_DAYS)
        await tariff_repository.update_subscription({
            'user_id': user_id, 'tariff_id': constants.tariff_free_trail_id, 'end_date': end_date,
            'trial_was_activated': True})
        return end_date

    @staticmethod
    async def _apply_groups(user_id: int):
        """Groups on or off by the tariff again, now that the free group is withheld or given back."""
        info = await Tariff.user_tariff_info(user_id)
        await tariff_repository.update_user_moderated_chats(user_id, info['channels_count'])

    @staticmethod
    async def free_group_withheld(user_id: int) -> bool:
        return await channel_bonus_repository.free_group_withheld(user_id)

    @staticmethod
    def penalty_days(channels_count: int) -> int:
        """The share of the bonus a channel left takes: rounded up, so leaving all of them takes it all."""
        return math.ceil(BONUS_DAYS / max(channels_count, 1))

    @classmethod
    async def _penalize(cls, claim: dict, left: list[dict]) -> tuple[int, datetime.datetime | None]:
        """Days off the running term for the channels left that took none yet, only while the bonus days run (the
        BONUS_DAYS after the claim) and never more than is left of them: after that the bonus is spent, the free
        group pausing is all, and days paid for later are never touched. (days taken, the new end date); (0, None)
        when nothing was taken."""
        now = datetime.datetime.now()
        bonus_until = claim['claimed_at'] + datetime.timedelta(days=BONUS_DAYS)
        if now >= bonus_until:
            return 0, None
        info = await Tariff.user_tariff_info(claim['user_id'])
        if info['tariff_id'] == Tariff.FREE_TARIFF_ID or info['end_date'] is None \
                or info['end_date'] <= now:
            return 0, None  # no term to take from: the free group waits instead
        share = cls.penalty_days(len(claim['channel_ids']))
        days = 0
        for channel in left:
            penalized = await channel_bonus_repository.mark_penalized(claim['user_id'], channel['service_id'])
            if penalized is not None:
                days += max(min(share, BONUS_DAYS - share * (penalized - 1)), 0)
        days = min(days, math.ceil((bonus_until - now) / datetime.timedelta(days=1)))
        if days <= 0:
            return 0, None
        end_date = await tariff_repository.take_days(claim['user_id'], days)
        return (days, end_date) if end_date is not None else (0, None)

    @classmethod
    async def check_claim(cls, claim: dict, notify, known: dict[str, bool] | None = None) -> None:
        """Unsubscribed: the free group waits, the days for each channel left go, and they are told (by
        `notify(claim, channels, days, end_date)`); subscribed again: the free group is back. Not knowing changes
        nothing. `known` is what an event said about a channel, so it is not asked again."""
        known = known or {}
        listed = {c['service_id']: c for c in await channel_bonus_repository.channels()}
        channels = [listed[i] for i in claim['channel_ids'] if i in listed]

        async def subscribed_to(channel: dict) -> bool | None:
            if channel['service_id'] in known:
                return known[channel['service_id']]
            return await cls.is_subscribed(channel['service_id'], claim['service_id'])

        found = await asyncio.gather(*(subscribed_to(c) for c in channels))
        was_lost = claim['lost_at'] is not None
        # Seen out of a channel: lost; not knowing about one (the bot lost it): as it was
        lost = True if False in found else was_lost if None in found else False
        await channel_bonus_repository.set_lost(claim['user_id'], lost)
        left = [c for c, subscribed in zip(channels, found) if subscribed is False]
        days, end_date = await cls._penalize(claim, left)
        if lost != was_lost:
            await cls._apply_groups(claim['user_id'])
        if lost and (not was_lost or days):
            await notify(claim, left, days, end_date)

    @classmethod
    async def recheck_round(cls, notify) -> None:
        """Checks the takers not checked for a day (check_claim)."""
        for claim in await channel_bonus_repository.claims_to_check(CHECKS_PER_ROUND):
            try:
                await cls.check_claim(claim, notify)
            except Exception as e:
                logger.error(e, 'Channel bonus: cannot check', claim['user_id'])

    @classmethod
    async def membership_changed(cls, channel_service_id: str, user_service_id: int | str, subscribed: bool,
                                 notify) -> None:
        """Someone joined or left a channel the bot is an admin of: if they took the bonus for it, check them."""
        claim = await channel_bonus_repository.claim_of(user_service_id)
        if claim is None or channel_service_id not in claim['channel_ids']:
            return
        await cls.check_claim(claim, notify, known={channel_service_id: subscribed})
