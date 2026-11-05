"""Messages of the way in through the bot (pkg/service/access.py): a request to the group's managers, with one-tap
answers, and the answer, or the end of a term, to the member."""
import html
import json

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from framework.system import telegram_exceptions
from framework.system.bot_setup import bot
from lib.language import localization
from pkg.repository import chat_repository
from pkg.service import access
from pkg.service.member_alerts import TIMED_DAYS, format_date, member_label
from pkg.service.tariff import Tariff
from pkg.service.user import User
from pkg.service.user_storage import UserStorage
from pkg.system.logger import logger


def callback(data: dict) -> str:
    return json.dumps(data, separators=(',', ':'))


def _button(text: str, data: dict) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=callback(data))


def request_member(request: dict) -> str:
    return member_label(request.get('nickname'), request.get('display_name'), request.get('user_service_id'))


def request_text(chat: dict, request: dict, language_code: str | None, reminder: bool = False) -> str:
    chat_name = html.escape(chat.get('name') or '')
    if request['kind'] == 'request':
        text = localization.get_message(['access', 'alert', 'request'], language_code, chat_name=chat_name,
                                        member=request_member(request))
    else:
        plan = {'days': request['days'] or 0, 'amount': request['amount'], 'currency': request['currency']}
        text = localization.get_message(['access', 'alert', 'paid'], language_code, chat_name=chat_name,
                                        member=request_member(request), plan=access.plan_text(plan, language_code))
    if reminder:
        text += "\n\n" + localization.get_message(['access', 'alert', 'reminder'], language_code)
    return text


def request_markup(chat: dict, request: dict, language_code: str | None, paid: bool = True) -> InlineKeyboardMarkup:
    """A paid request: confirm the term paid for. A free one: for good, or for a week or a month."""
    def text(key: str, **kwargs) -> str:
        return localization.get_message(['access', 'alert', 'buttons', key], language_code, **kwargs)

    if request['kind'] != 'request' and request['days'] is not None:
        rows = [[_button(text('confirm', term=access.days_text(request['days'], language_code)),
                         {'tp': 'ar', 'r': request['id'], 'd': request['days']})]]
    else:
        rows = [[_button(text('forever'), {'tp': 'ar', 'r': request['id'], 'd': 0})],
                # A term is a paid feature: locked on the free tariff, as on the group's page
                [_button(('' if paid else '🔒 ') + text('days', days=days), {'tp': 'ar', 'r': request['id'], 'd': days})
                 for days in TIMED_DAYS]]
    rows.append([_button(text('reject'), {'tp': 'aj', 'r': request['id']}),
                 _button(localization.get_message(['alerts', 'buttons', 'group'], language_code),
                         {'tp': 'chat', 'id': chat['id']})])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def _send(service_id: str | int, text: str, markup: InlineKeyboardMarkup | None) -> bool:
    try:
        await bot.send_message(int(service_id), text, parse_mode='HTML', reply_markup=markup,
                               disable_web_page_preview=True)
        # The next screen of the menu is a new message below this one, not an edit of an older one
        UserStorage.set_resend(int(service_id))
        return True
    except (telegram_exceptions.TelegramForbiddenError, telegram_exceptions.TelegramBadRequest) as e:
        logger.warning('Cannot send an access message to', service_id, e)
        return False


async def send_request(chat: dict, request: dict, reminder: bool = False, only_to: int | None = None) -> None:
    """The request to every manager of the group (or to one of them, when they asked for the list)."""
    paid = Tariff.is_paid(await chat_repository.owner_tariff_id(chat['id']))
    for user in await chat_repository.managers(chat['id']):
        if only_to is not None and int(user['service_id']) != only_to:
            continue
        language_code = user['language_code']
        await _send(user['service_id'], request_text(chat, request, language_code, reminder),
                    request_markup(chat, request, language_code, paid))


def _member_language(request: dict, user: dict | None) -> str | None:
    return (user or {}).get('language_code') or request.get('language_code')


def open_group_markup(chat: dict, nickname: str | None, language_code: str | None) -> InlineKeyboardMarkup | None:
    if not nickname:
        return None
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(
        text=localization.get_message(['access', 'member', 'buttons', 'open_group'], language_code),
        url=f"https://t.me/{nickname}")]])


async def tell_member_decision(chat: dict, request: dict, entry: dict | None, approved: bool,
                               chat_nickname: str | None = None) -> None:
    user = await User.find_by_service_id(int(request['user_service_id']))
    language_code = _member_language(request, user)
    chat_name = html.escape(chat.get('name') or '')
    if approved:
        if entry is not None and entry.get('expires_at') is not None:
            text = localization.get_message(['access', 'member', 'approved_until'], language_code,
                                            chat_name=chat_name, date=format_date(entry['expires_at']))
        else:
            text = localization.get_message(['access', 'member', 'approved_forever'], language_code,
                                            chat_name=chat_name)
    else:
        key = 'rejected' if request['kind'] == 'request' else 'rejected_paid'
        text = localization.get_message(['access', 'member', key], language_code, chat_name=chat_name)
    await _send(request['user_service_id'], text,
                open_group_markup(chat, chat_nickname, language_code) if approved else None)


async def remind_member(entry: dict, stage_key: str) -> None:
    """A day before a timed access ends, and when it has: the member hears it too, with a way to extend, when the
    group lets people in through the bot and the member has started the bot."""
    if entry.get('access_mode', 'off') == 'off' or not entry.get('user_service_id'):
        return
    user = await User.find_by_service_id(int(entry['user_service_id']))
    if user is None:
        return
    language_code = user['language_code']
    text = localization.get_message(
        ['access', 'member', 'expiry_soon' if stage_key == 'soon' else 'expiry_ended'], language_code,
        chat_name=html.escape(entry.get('chat_name') or ''), date=format_date(entry['expires_at']))
    button = 'renew' if entry['access_mode'] == 'paid' else 'ask_again'
    markup = InlineKeyboardMarkup(inline_keyboard=[[_button(
        localization.get_message(['access', 'member', 'buttons', button], language_code),
        {'tp': 'jo', 'c': entry['chat_id']})]])
    await _send(entry['user_service_id'], text, markup)
