"""The way in through the bot (pkg/service/access.py), outside the menu's navigation:

- the member's page of a group (opened by the link j_<group id>): ask, or pick a term and pay, then "I paid";
- the managers' answers under a request: approve (for the term paid for, for good, for a week or a month) or
  decline.

Callback data: jo (the page), jp (a term), js (send the request), jr (remind the owner); ar (approve), aj
(decline)."""
import datetime
import html

from aiogram import Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from framework.system import telegram_exceptions, telegram_types
from lib.language import localization
from pkg.controller.routers.quick_actions_router import QuickAction, _managed_chat, lift_restriction
from pkg.service import access
from pkg.service.access import Requests
from pkg.service.access_messages import callback, request_member, send_request, tell_member_decision
from pkg.service.allowed_user import full_name
from pkg.service.chat import Chat
from pkg.service.member_alerts import format_date, save_token
from pkg.service.tariff import Tariff
from pkg.system.logger import logger
from project import constants


def _text(path: list, language_code: str | None, **kwargs) -> str:
    return localization.get_message(['access', *path], language_code, **kwargs)


def _button(text: str, data: dict | None = None, url: str | None = None) -> InlineKeyboardButton:
    if url is not None:
        return InlineKeyboardButton(text=text, url=url)
    return InlineKeyboardButton(text=text, callback_data=callback(data))


def _recent(moment: datetime.datetime | None) -> bool:
    return moment is not None and moment > datetime.datetime.now() - access.REPEAT_AFTER


async def member_page(chat_id: int, user, language_code: str | None) -> tuple[str, InlineKeyboardMarkup | None]:
    """The group as a member off its whitelist sees it: the owner's terms, then what they can do now."""
    chat = await Chat.find(chat_id)
    if chat is None:
        return _text(['member', 'not_found'], language_code), None
    mode = access.effective_mode(chat, await Chat.owner_tariff_id(chat['id']))
    if mode == 'off':
        return _text(['member', 'off'], language_code), None

    current = await access.current_access(chat['id'], str(user.id), user.username)
    lines = [_text(['member', 'title'], language_code, chat_name=html.escape(await Chat.name_of(chat)))]
    if current is None:
        lines.append(_text(['member', 'intro'], language_code))
    if chat.get('access_terms'):
        lines.append(f"<blockquote>{html.escape(chat['access_terms'])}</blockquote>")

    rows = []

    def plan_rows():
        return [[_button(access.plan_text(plan, language_code), {'tp': 'jp', 'c': chat['id'], 'd': plan['days']})]
                for plan in access.plans_of(chat)]

    latest = await Requests.latest(chat['id'], str(user.id))
    pending = latest is not None and latest['status'] == 'pending'
    if current is not None:
        if current['expires_at'] is None:
            lines.append(_text(['member', 'have_forever'], language_code))
        else:
            lines.append(_text(['member', 'have_until'], language_code, date=format_date(current['expires_at'])))
            if mode == 'paid' and not pending:
                lines.append(_text(['member', 'extend_hint'], language_code))
                rows += plan_rows()
    if pending and (current is None or current['expires_at'] is not None):
        date = format_date(latest['created_at'])
        if latest['kind'] == 'request':
            lines.append(_text(['member', 'pending'], language_code, date=date))
        else:
            plan = {'days': latest['days'] or 0, 'amount': latest['amount'], 'currency': latest['currency']}
            lines.append(_text(['member', 'pending_paid'], language_code, date=date,
                               plan=access.plan_text(plan, language_code)))
        # Reminding is offered once the owner has had some hours to answer
        if not _recent(latest['reminded_at'] or latest['created_at']):
            rows.append([_button(_text(['member', 'buttons', 'remind'], language_code),
                                 {'tp': 'jr', 'c': chat['id']})])
    elif current is not None:
        pass
    elif latest is not None and latest['status'] == 'rejected' and _recent(latest['decided_at']):
        lines.append(_text(['member', 'rejected_recently'], language_code, date=format_date(latest['decided_at'])))
    elif mode == 'request':
        lines.append(_text(['member', 'request_hint'], language_code))
        rows.append([_button(_text(['member', 'buttons', 'request'], language_code),
                             {'tp': 'js', 'c': chat['id'], 'd': -1})])
    else:
        lines.append(_text(['member', 'paid_hint'], language_code))
        rows += plan_rows()

    lines.append(_text(['member', 'footer'], language_code, bot=constants.bot_nickname))
    return "\n\n".join(lines), InlineKeyboardMarkup(inline_keyboard=rows) if rows else None


async def open_join_page(message: telegram_types.Message, chat_id: int, language_code: str | None) -> None:
    """The link j_<group id>: the group's page for a member, as a new message."""
    text, markup = await member_page(chat_id, message.from_user, language_code)
    await message.answer(text, parse_mode='HTML', reply_markup=markup, disable_web_page_preview=True)


async def _edit(call: CallbackQuery, text: str, markup: InlineKeyboardMarkup | None):
    try:
        await call.message.edit_text(text, parse_mode='HTML', reply_markup=markup, disable_web_page_preview=True)
    except telegram_exceptions.TelegramBadRequest as e:
        if 'message is not modified' not in str(e):
            logger.warning('Cannot edit an access message', e)


async def _show_page(call: CallbackQuery, chat_id: int):
    text, markup = await member_page(chat_id, call.from_user, call.from_user.language_code)
    await _edit(call, text, markup)


def access_router() -> Router:
    router = Router()

    # The member's side

    @router.callback_query(QuickAction('jo'))
    async def page(call: CallbackQuery, data: dict):
        await _show_page(call, int(data.get('c') or 0))
        await call.answer()

    @router.callback_query(QuickAction('jp'))
    async def plan(call: CallbackQuery, data: dict):
        language_code = call.from_user.language_code
        chat = await Chat.find(int(data.get('c') or 0))
        chosen = access.plan_for(chat, int(data.get('d') or 0)) if chat else None
        if chosen is None or access.effective_mode(chat, await Chat.owner_tariff_id(chat['id'])) != 'paid':
            await call.answer(_text(['member', 'toasts', 'unavailable'], language_code), show_alert=True)
            if chat is not None:
                await _show_page(call, chat['id'])
            return

        chat_name = html.escape(await Chat.name_of(chat))
        plan_text = access.plan_text(chosen, language_code)
        url = access.payment_url(chat)
        if url is not None:
            text = _text(['member', 'plan'], language_code, chat_name=chat_name, plan=plan_text)
        else:
            text = _text(['member', 'plan_details'], language_code, chat_name=chat_name, plan=plan_text,
                         payment=html.escape(chat.get('access_payment') or ''))
        text += "\n\n" + _text(['member', 'plan_note'], language_code)
        rows = []
        if url is not None:
            rows.append([_button(_text(['member', 'buttons', 'pay'], language_code,
                                       amount=access.format_amount(chosen['amount'], chosen['currency'])), url=url)])
        rows.append([_button(_text(['member', 'buttons', 'paid'], language_code),
                             {'tp': 'js', 'c': chat['id'], 'd': chosen['days']})])
        rows.append([_button(_text(['member', 'buttons', 'back'], language_code), {'tp': 'jo', 'c': chat['id']})])
        await _edit(call, text, InlineKeyboardMarkup(inline_keyboard=rows))
        await call.answer()

    @router.callback_query(QuickAction('js'))
    async def send(call: CallbackQuery, data: dict):
        language_code = call.from_user.language_code
        chat = await Chat.find(int(data.get('c') or 0))
        if chat is None:
            await call.answer(_text(['member', 'not_found'], language_code), show_alert=True)
            return
        mode = access.effective_mode(chat, await Chat.owner_tariff_id(chat['id']))
        days = int(data.get('d') if data.get('d') is not None else -1)
        chosen = access.plan_for(chat, days) if days >= 0 else None
        if (days < 0 and mode != 'request') or (days >= 0 and (mode != 'paid' or chosen is None)):
            await call.answer(_text(['member', 'toasts', 'unavailable'], language_code), show_alert=True)
            await _show_page(call, chat['id'])
            return

        sender = call.from_user
        request = await Requests.create({
            'moderated_chat_id': chat['id'], 'user_service_id': str(sender.id), 'nickname': sender.username,
            'display_name': full_name(sender), 'language_code': language_code,
            'kind': 'request' if chosen is None else 'paid_manual',
            'days': None if chosen is None else chosen['days'],
            'amount': None if chosen is None else chosen['amount'],
            'currency': None if chosen is None else chosen['currency'],
            'provider': None if chosen is None else 'link'})
        if request is None:
            await call.answer(_text(['member', 'toasts', 'already'], language_code), show_alert=True)
        else:
            await send_request({**chat, 'name': await Chat.name_of(chat)}, request)
            await call.answer(_text(['member', 'toasts', 'sent'], language_code))
        await _show_page(call, chat['id'])

    @router.callback_query(QuickAction('jr'))
    async def remind(call: CallbackQuery, data: dict):
        language_code = call.from_user.language_code
        chat = await Chat.find(int(data.get('c') or 0))
        latest = await Requests.latest(chat['id'], str(call.from_user.id)) if chat else None
        if latest is None or latest['status'] != 'pending':
            if chat is not None:
                await _show_page(call, chat['id'])
            await call.answer()
            return
        if _recent(latest['reminded_at'] or latest['created_at']):
            await call.answer(_text(['member', 'toasts', 'too_soon'], language_code), show_alert=True)
            return
        await Requests.update(latest['id'], {'reminded_at': datetime.datetime.now()})
        await send_request({**chat, 'name': await Chat.name_of(chat)}, latest, reminder=True)
        await call.answer(_text(['member', 'toasts', 'reminded'], language_code))

    # The managers' side

    async def _decision(call: CallbackQuery, data: dict) -> tuple[dict, dict] | None:
        language_code = call.from_user.language_code
        request = await Requests.find(int(data.get('r') or 0))
        if request is None:
            await call.answer(localization.get_message(['alerts', 'expired'], language_code), show_alert=True)
            return None
        chat = await _managed_chat(call, request['moderated_chat_id'], language_code)
        if chat is None:
            return None
        if request['status'] != 'pending':
            await _edit(call, _text(['alert', 'decided'], language_code), None)
            await call.answer()
            return None
        return request, {**chat, 'name': await Chat.name_of(chat)}

    @router.callback_query(QuickAction('ar'))
    async def approve(call: CallbackQuery, data: dict):
        language_code = call.from_user.language_code
        found = await _decision(call, data)
        if found is None:
            return
        request, chat = found
        days = int(data.get('d') or 0)
        if days and not Tariff.is_paid(await Chat.owner_tariff_id(chat['id'])):
            await call.answer(localization.get_message(['alerts', 'paid_only'], language_code), show_alert=True)
            return
        if await Requests.decide(request['id'], 'approved', str(call.from_user.id)) is None:
            await _edit(call, _text(['alert', 'decided'], language_code), None)
            await call.answer()
            return

        before = await access.current_access(chat['id'], request['user_service_id'], request['nickname'])
        entry = await access.grant(chat['id'], request['user_service_id'], request['nickname'],
                                   request['display_name'], days)
        await lift_restriction(int(chat['service_id']), int(request['user_service_id']))

        member, chat_name = request_member(request), html.escape(chat['name'])
        if entry is not None and entry.get('expires_at') is not None:
            text = _text(['alert', 'approved_until'], language_code, member=member, chat_name=chat_name,
                         date=format_date(entry['expires_at']))
        else:
            text = _text(['alert', 'approved_forever'], language_code, member=member, chat_name=chat_name)
        row = [_button(localization.get_message(['alerts', 'buttons', 'group'], language_code),
                       {'tp': 'chat', 'id': chat['id']})]
        if before is None:
            # Undo, the same as under an alert about a stranger; not for an extension, which it would wipe out
            token = save_token({'c': chat['id'], 'u': request['user_service_id'], 'n': request['nickname'],
                                'name': request['display_name']})
            row.insert(0, _button(localization.get_message(['alerts', 'buttons', 'undo'], language_code),
                                  {'tp': 'qu', 'k': token}))
        await _edit(call, text, InlineKeyboardMarkup(inline_keyboard=[row]))
        await call.answer(_text(['alert', 'approved_toast'], language_code))

        chat_info = await Chat.load_info(str(chat['service_id']))
        await tell_member_decision(chat, request, entry, True, chat_info.get('nickname'))

    @router.callback_query(QuickAction('aj'))
    async def reject(call: CallbackQuery, data: dict):
        language_code = call.from_user.language_code
        found = await _decision(call, data)
        if found is None:
            return
        request, chat = found
        if await Requests.decide(request['id'], 'rejected', str(call.from_user.id)) is None:
            await _edit(call, _text(['alert', 'decided'], language_code), None)
            await call.answer()
            return
        await _edit(call, _text(['alert', 'rejected'], language_code, member=request_member(request),
                                chat_name=html.escape(chat['name'])), None)
        await call.answer(_text(['alert', 'rejected_toast'], language_code))
        await tell_member_decision(chat, request, None, False)

    return router
