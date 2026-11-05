"""The buttons under alerts (pkg/service/member_alerts.py): allow a member for good or for a while, undo, mute
or unmute a group's alerts. They work from any message, outside the menu's navigation."""
import html
import json

from aiogram import Router
from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from framework.system import telegram_exceptions, telegram_types
from framework.system.bot_setup import bot
from lib.language import localization
from pkg.service.allowed_user import AllowedUser
from pkg.service.chat import Chat
from pkg.service.member_alerts import access_buttons, load_token, member_label, format_date
from pkg.service.tariff import Tariff
from pkg.system.logger import logger


class QuickAction(BaseFilter):
    def __init__(self, *types: str):
        self.types = types

    async def __call__(self, call: CallbackQuery) -> dict | bool:
        try:
            data = json.loads(call.data or '')
        except ValueError:
            return False
        if not isinstance(data, dict) or data.get('tp') not in self.types:
            return False
        return {'data': data}


def _callback(data: dict) -> str:
    return json.dumps(data, separators=(',', ':'))


async def _edit(call: CallbackQuery, text: str, markup: InlineKeyboardMarkup | None):
    try:
        await call.message.edit_text(text, parse_mode='HTML', reply_markup=markup, disable_web_page_preview=True)
    except telegram_exceptions.TelegramBadRequest as e:
        if 'message is not modified' not in str(e):
            logger.warning('Cannot edit an alert', e)


async def _managed_chat(call: CallbackQuery, chat_id: int, language_code: str | None) -> dict | None:
    """The group, if the one who tapped manages it in the bot; otherwise they are told why not."""
    chat = await Chat.find(chat_id)
    if chat is None:
        await call.answer(localization.get_message(['chat', 'errors', 'not_found'], language_code), show_alert=True)
        return None
    if not await Chat.is_manager(chat['id'], call.from_user.id):
        await call.answer(localization.get_message(['alerts', 'not_yours'], language_code), show_alert=True)
        return None
    return chat


async def lift_restriction(chat_service_id: int, user_service_id: int):
    """The member just allowed was muted for a while after their message: let them write at once."""
    try:
        await bot.restrict_chat_member(
            chat_service_id, user_service_id,
            permissions=telegram_types.ChatPermissions(**{
                name: True for name in telegram_types.ChatPermissions.model_fields if name.startswith('can_')}))
    except (telegram_exceptions.TelegramBadRequest, telegram_exceptions.TelegramForbiddenError) as e:
        logger.warning('Cannot lift a restriction', e)


def quick_actions_router() -> Router:
    router = Router()

    @router.callback_query(QuickAction('qa'))
    async def allow(call: CallbackQuery, data: dict):
        language_code = call.from_user.language_code
        payload = load_token(str(data.get('k', '')))
        if payload is None:
            await call.answer(localization.get_message(['alerts', 'expired'], language_code), show_alert=True)
            return
        chat = await _managed_chat(call, payload['c'], language_code)
        if chat is None:
            return

        days = int(data.get('d') or 0)
        if days and not Tariff.is_paid(await Chat.owner_tariff_id(chat['id'])):
            await call.answer(localization.get_message(['alerts', 'paid_only'], language_code), show_alert=True)
            return

        entry = await AllowedUser.allow(chat['id'], payload.get('u'), payload.get('n'), payload.get('name'), days)
        if entry is None:
            await call.answer(localization.get_message(['errors', 'unexpected'], language_code), show_alert=True)
            return
        if payload.get('u'):
            await lift_restriction(int(chat['service_id']), int(payload['u']))

        member = member_label(payload.get('n'), payload.get('name'), payload.get('u'))
        chat_name = html.escape(chat.get('name') or '')
        if entry.get('expires_at') is not None:
            result = localization.get_message(['alerts', 'allowed_until'], language_code, member=member,
                                              chat_name=chat_name, date=format_date(entry['expires_at']))
        else:
            result = localization.get_message(['alerts', 'allowed'], language_code, member=member,
                                              chat_name=chat_name)
        await _edit(call, result, InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text=localization.get_message(['alerts', 'buttons', 'undo'], language_code),
                                 callback_data=_callback({'tp': 'qu', 'k': data['k']})),
            InlineKeyboardButton(text=localization.get_message(['alerts', 'buttons', 'group'], language_code),
                                 callback_data=_callback({'tp': 'chat', 'id': chat['id']})),
        ]]))
        await call.answer(localization.get_message(['alerts', 'allowed_toast'], language_code))

    @router.callback_query(QuickAction('qu'))
    async def undo(call: CallbackQuery, data: dict):
        language_code = call.from_user.language_code
        payload = load_token(str(data.get('k', '')))
        if payload is None:
            await call.answer(localization.get_message(['alerts', 'expired'], language_code), show_alert=True)
            return
        chat = await _managed_chat(call, payload['c'], language_code)
        if chat is None:
            return
        await AllowedUser.disallow(chat['id'], payload.get('u'), payload.get('n'))
        member = member_label(payload.get('n'), payload.get('name'), payload.get('u'))
        await _edit(call, localization.get_message(
            ['alerts', 'undone'], language_code, member=member, chat_name=html.escape(chat.get('name') or '')),
            access_buttons(data['k'], chat['id'], language_code))
        await call.answer()

    @router.callback_query(QuickAction('qm', 'qn'))
    async def mute(call: CallbackQuery, data: dict):
        language_code = call.from_user.language_code
        chat = await _managed_chat(call, int(data.get('c') or 0), language_code)
        if chat is None:
            return
        enabled = data['tp'] == 'qn'
        await Chat.update_settings(chat['id'], {'owner_alerts': enabled})
        chat_name = html.escape(chat.get('name') or '')
        if enabled:
            await _edit(call, localization.get_message(['alerts', 'unmuted'], language_code, chat_name=chat_name),
                        None)
        else:
            await _edit(call, localization.get_message(['alerts', 'muted'], language_code, chat_name=chat_name),
                        InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(
                            text=localization.get_message(['alerts', 'buttons', 'unmute'], language_code),
                            callback_data=_callback({'tp': 'qn', 'c': chat['id']}))]]))
        await call.answer()

    return router
