"""Messages to the people who manage a group: who tried to write, whose timed access ends. Each comes with
one-tap buttons (allow, allow for a while, open the group, mute), handled by the quick actions router.

A button cannot carry a nickname and a name (64 bytes of callback data), so it carries a short token for an
entry in Redis that holds them."""
import datetime
import html
import json
import secrets

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from framework.repository.storage_connection import Storage
from framework.system import telegram_exceptions
from framework.system.bot_setup import bot
from lib.language import localization
from pkg.repository import allowed_user_repository, chat_repository
from pkg.service.allowed_user import full_name
from pkg.service.user_storage import UserStorage
from pkg.system.logger import logger

TOKEN_TTL_SECONDS = 30 * 86400
# One alert per member and group a day, and no more than this many alerts per group a day
MEMBER_ALERT_INTERVAL_SECONDS = 86400
GROUP_ALERTS_PER_DAY = 10
PREVIEW_LENGTH = 300
TIMED_DAYS = (7, 30)


def member_label(nickname: str | None, display_name: str | None, user_service_id: str | int | None) -> str:
    """How a member is shown (HTML): their name linking to them, and the @nickname."""
    name = html.escape(display_name or '') or None
    parts = []
    if name and user_service_id:
        parts.append(f'<a href="tg://user?id={user_service_id}">{name}</a>')
    elif name:
        parts.append(name)
    if nickname:
        parts.append(f'@{html.escape(nickname)}')
    if not parts:
        parts.append(f'id {user_service_id}')
    return ' '.join(parts)


def format_date(moment: datetime.datetime) -> str:
    return moment.strftime('%d.%m.%Y')


def save_token(payload: dict) -> str:
    token = secrets.token_urlsafe(6)
    Storage().connection.set(f'qa:{token}', json.dumps(payload), ex=TOKEN_TTL_SECONDS)
    return token


def load_token(token: str) -> dict | None:
    raw = Storage().connection.get(f'qa:{token}')
    return json.loads(raw) if raw else None


def _callback(data: dict) -> str:
    return json.dumps(data, separators=(',', ':'))


def access_buttons(token: str, chat_id: int, language_code: str, renew: bool = False) -> InlineKeyboardMarkup:
    """Allow for good, for a week, for a month; the group's page; mute the group's alerts."""
    prefix = 'renew' if renew else 'allow'
    rows = [
        [InlineKeyboardButton(
            text=localization.get_message(['alerts', 'buttons', f'{prefix}_forever'], language_code),
            callback_data=_callback({'tp': 'qa', 'k': token, 'd': 0}))],
        [InlineKeyboardButton(
            text=localization.get_message(['alerts', 'buttons', f'{prefix}_days'], language_code, days=days),
            callback_data=_callback({'tp': 'qa', 'k': token, 'd': days})) for days in TIMED_DAYS],
        [InlineKeyboardButton(
            text=localization.get_message(['alerts', 'buttons', 'group'], language_code),
            callback_data=_callback({'tp': 'chat', 'id': chat_id})),
         InlineKeyboardButton(
            text=localization.get_message(['alerts', 'buttons', 'mute'], language_code),
            callback_data=_callback({'tp': 'qm', 'c': chat_id}))],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def _send(user: dict, text: str, markup: InlineKeyboardMarkup | None):
    try:
        await bot.send_message(int(user['service_id']), text, parse_mode='HTML', reply_markup=markup,
                               disable_web_page_preview=True)
        # The next screen of the menu is a new message below the alert, not an edit of an older one
        UserStorage.set_resend(int(user['service_id']))
    except (telegram_exceptions.TelegramForbiddenError, telegram_exceptions.TelegramBadRequest) as e:
        logger.warning('Cannot send an alert to', user['service_id'], e)


class MemberAlerts:
    @staticmethod
    def _rate_allows(chat_id: int, user_service_id: int) -> bool:
        connection = Storage().connection
        if not connection.set(f'alert:{chat_id}:{user_service_id}', 1, nx=True, ex=MEMBER_ALERT_INTERVAL_SECONDS):
            return False
        day_key = f'alerts:{chat_id}:{datetime.date.today()}'
        sent_today = connection.incr(day_key)
        if sent_today == 1:
            connection.expire(day_key, 2 * 86400)
        return sent_today <= GROUP_ALERTS_PER_DAY

    @staticmethod
    async def removed(chat_data: dict, message) -> None:
        """A member off the whitelist wrote and the message went: tell the group's managers, with the text, so
        that letting them in is one tap."""
        if not chat_data.get('owner_alerts', True):
            return
        # The group lets people in through the bot: they ask themselves, the managers get their requests
        if (chat_data.get('access_mode') or 'off') != 'off':
            return
        sender = message.from_user
        if not MemberAlerts._rate_allows(chat_data['id'], sender.id):
            return

        token = save_token({
            'c': chat_data['id'], 'u': str(sender.id), 'n': sender.username, 'name': full_name(sender)})
        member = member_label(sender.username, full_name(sender), sender.id)
        chat_name = html.escape(chat_data.get('name') or message.chat.title or '')
        preview = (message.text or message.caption or '').strip()
        if len(preview) > PREVIEW_LENGTH:
            preview = preview[:PREVIEW_LENGTH] + '…'

        for user in await chat_repository.managers(chat_data['id']):
            language_code = user['language_code']
            text = localization.get_message(
                ['alerts', 'removed', 'text'], language_code, member=member, chat_name=chat_name)
            if preview:
                text += f"\n\n<blockquote>{html.escape(preview)}</blockquote>"
            else:
                text += "\n\n" + localization.get_message(['alerts', 'removed', 'no_text'], language_code)
            text += "\n\n" + localization.get_message(['alerts', 'removed', 'hint'], language_code)
            await _send(user, text, access_buttons(token, chat_data['id'], language_code))

    @staticmethod
    async def expiry_round(now: datetime.datetime | None = None) -> None:
        """Part of the hourly round: a day before a timed access ends the managers are reminded, and told when
        it has ended, each with buttons to give more time."""
        now = now or datetime.datetime.now()
        for stage, until, key in ((1, now + datetime.timedelta(days=1), 'soon'), (2, now, 'ended')):
            for entry in await allowed_user_repository.expiring(stage, until):
                if stage == 1 and entry['expires_at'] <= now:
                    continue  # past already: the "ended" pass tells it
                token = save_token({'c': entry['chat_id'], 'u': entry['user_service_id'], 'n': entry['nickname'],
                                    'name': entry['display_name']})
                member = member_label(entry['nickname'], entry['display_name'], entry['user_service_id'])
                for user in await chat_repository.managers(entry['chat_id']):
                    language_code = user['language_code']
                    text = localization.get_message(
                        ['alerts', 'expiry', key], language_code, member=member,
                        chat_name=html.escape(entry['chat_name'] or ''), date=format_date(entry['expires_at']))
                    await _send(user, text, access_buttons(token, entry['chat_id'], language_code, renew=True))
                # The member too, with a way to extend, when the group lets people in through the bot
                from pkg.service.access_messages import remind_member
                await remind_member(dict(entry), key)
                await allowed_user_repository.mark_expiry_notice(entry['id'], stage)
