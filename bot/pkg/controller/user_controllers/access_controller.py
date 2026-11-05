"""The owner's page of the way in through the bot (pkg/service/access.py), under the group's page.

Off: two choices, by request (free) or paid (a paid tariff). Choosing paid walks through the prices and the way
to pay, one prompt after another, on the same page. Texts (prices, the way to pay, the terms) are typed in
reply to a prompt; the page waits for them in the state data of the route ('editing')."""
import html
import json

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from framework.controller import state_data
from framework.controller.message_tools import go_back_inline_button, message_sender, notify
from framework.controller.types import ControllerParams
from framework.system import telegram_exceptions
from framework.system.bot_setup import bot
from lib.language import localization
from pkg.controller.user_controllers.common_controller import raise_error
from pkg.service import access
from pkg.service.access import Requests
from pkg.service.access_messages import send_request
from pkg.service.access_providers import cryptobot
from pkg.service.secret_box import seal
from pkg.service.chat import Chat
from pkg.service.tariff import Tariff
from pkg.service.user_storage import UserStorage
from pkg.system.logger import logger

ROUTE = 'chat_access'
EDITABLE = ('prices', 'payment', 'terms', 'cryptobot')


def _text(path: list, language_code: str | None, **kwargs) -> str:
    return localization.get_message(['access', 'owner', *path], language_code, **kwargs)


def _button(text: str, data: dict) -> dict:
    return {'text': text, 'callback_data': data}


async def _chat(params: ControllerParams) -> dict | None:
    chat_state = state_data.get_local_state_data(params['message'], 'chat')
    if not chat_state or 'id' not in chat_state:
        await raise_error(None, params['message'], 'state_data_none')
        return None
    return await Chat.find(chat_state['id'])


def _editing(params: ControllerParams) -> str | None:
    editing = (params['state_data'] or {}).get('editing')
    return editing if editing in EDITABLE else None


def _set_editing(params: ControllerParams, editing: str | None):
    UserStorage.add_user_state_data(params['message'].chat.id, ROUTE, {'editing': editing} if editing else {})
    params['state_data'] = {'editing': editing} if editing else {}


def _wizard_step(chat: dict, editing: str) -> int | None:
    """Setting up paid entry for the first time: prices are step 1 of 2, the way to pay step 2."""
    if (chat.get('access_mode') or 'off') != 'paid':
        return None
    if editing == 'prices' and not access.plans_of(chat):
        return 1
    if editing in ('payment', 'cryptobot') and not access.ready_to_pay(chat):
        return 2
    return None


async def _render(params: ControllerParams, chat: dict, notice: str | None = None):
    language_code = params['language_code']
    editing = _editing(params)
    mode = chat.get('access_mode') or 'off'
    tariff_id = await Chat.owner_tariff_id(chat['id'])
    paid_tariff = Tariff.is_paid(tariff_id)
    chat_name = html.escape(await Chat.name_of(chat))

    lines = [_text(['title'], language_code, chat_name=chat_name)]
    if notice:
        lines.insert(0, notice)
    rows = []

    def button(key: str, data: dict, **kwargs) -> dict:
        return _button(_text(['buttons', key], language_code, **kwargs), data)

    if mode == 'off':
        lines.append(_text(['intro_off'], language_code))
        lock = '' if paid_tariff else _text(['buttons', 'locked'], language_code)
        rows += [[button('mode_request', {'tp': 'acc_mode', 'm': 'request'})],
                 [_button(lock + _text(['buttons', 'mode_paid'], language_code), {'tp': 'acc_mode', 'm': 'paid'})]]
    else:
        lines.append(_text(['mode', mode], language_code))
        if mode == 'paid':
            plans = access.plans_of(chat)
            lines.append(_text(['prices'], language_code, plans=' · '.join(
                access.plan_text(plan, language_code) for plan in plans)) if plans
                else _text(['prices_none'], language_code))
            provider = chat.get('access_provider') or 'link'
            payment = chat.get('access_payment')
            if provider != 'link' and access.ready_to_pay(chat):
                lines.append(_text(['payment_provider', provider], language_code,
                                   label=html.escape(chat.get('access_provider_label') or '')))
            elif provider == 'link' and payment:
                lines.append(_text(['payment'], language_code, payment=html.escape(payment)))
            else:
                lines.append(_text(['payment_none'], language_code))
        terms = chat.get('access_terms')
        lines.append(_text(['terms'], language_code, terms=html.escape(terms)) if terms
                     else _text(['terms_none'], language_code))
        lines.append(_text(['link'], language_code, link=access.join_link(chat['id'])))
        pending = await Requests.pending_count(chat['id'])
        if pending:
            lines.append(_text(['pending'], language_code, count=pending))
        if mode == 'paid' and access.effective_mode(chat, tariff_id) != 'paid':
            lines.append(_text(['paid_fallback' if not paid_tariff else 'paid_incomplete'], language_code))
        if chat.get('everyone_can_write'):
            lines.append(_text(['everyone_note'], language_code))

        if mode == 'paid':
            rows.append([button('prices', {'tp': 'acc_edit', 'f': 'prices'}),
                         button('payment', {'tp': 'acc_edit', 'f': 'payment'})])
        rows.append([button('terms', {'tp': 'acc_edit', 'f': 'terms'}), button('post', {'tp': 'acc_post'})])
        if pending:
            rows.append([button('requests', {'tp': 'acc_requests'}, count=pending)])
        rows.append([button('to_request', {'tp': 'acc_mode', 'm': 'request'}) if mode == 'paid'
                     else button('to_paid', {'tp': 'acc_mode', 'm': 'paid'})])
        rows.append([button('off', {'tp': 'acc_mode', 'm': 'off'})])

    if editing:
        # Waiting for the text: the title, the step of the walk through paid entry, the prompt
        lines = lines[:2 if notice else 1]
        step = _wizard_step(chat, editing)
        if step:
            lines.append(_text(['step'], language_code, step=step))
        lines.append(_text(['prompt', editing], language_code, currency=access.CURRENCIES[
            access.default_currency(language_code)]['symbol']))
        rows = []
        if editing == 'payment':
            # A link is typed; a provider that confirms payments is picked
            rows.append([button('use_cryptobot', {'tp': 'acc_edit', 'f': 'cryptobot'})])
        elif editing == 'cryptobot':
            rows.append([button('other_ways', {'tp': 'acc_edit', 'f': 'payment'})])
        rows.append([button('cancel', {'tp': 'acc_cancel'})])
    else:
        rows.append([go_back_inline_button(language_code)])

    await message_sender(params['message'].chat.id, message_structures=[{
        'type': 'text', 'text': "\n\n".join(lines), 'reply_markup': rows, 'parse_mode': 'HTML',
        'disable_web_page_preview': True}])


async def page(params: ControllerParams):
    call, message = params['call'], params['message']
    chat = await _chat(params)
    if chat is None:
        await notify(call, message, localization.get_message(['chat', 'errors', 'not_found'],
                                                             params['language_code']))
        return False

    # A text typed in reply to a prompt
    if call is None and message.text is not None and not message.text.startswith('/'):
        editing = _editing(params)
        if editing is None:
            await _render(params, chat, notice=_text(['errors', 'not_editing'], params['language_code']))
            return
        await _save(params, chat, editing, message.text.strip())
        return

    # Opening the page (or coming back to it) drops a prompt left unanswered
    _set_editing(params, None)
    await _render(params, chat)


async def _save(params: ControllerParams, chat: dict, editing: str, text: str):
    language_code = params['language_code']

    def error(notice: str):
        return _render(params, chat, notice=notice)

    if editing == 'cryptobot':
        await _connect_cryptobot(params, chat, text)
        return

    if editing == 'prices':
        plans, bad = access.parse_plans(text, access.default_currency(language_code))
        if bad or not plans:
            await error(_text(['errors', 'prices_bad'], language_code,
                              lines=html.escape('\n'.join(bad or [text]))))
            return
        chat = await Chat.update_settings(chat['id'], {'access_plans': json.dumps(plans)})
        # The walk through paid entry: the way to pay comes next if there is none
        _set_editing(params, 'payment' if not access.ready_to_pay(chat) else None)
    else:
        limit = access.PAYMENT_LENGTH if editing == 'payment' else access.TERMS_LENGTH
        if len(text) > limit:
            await error(_text(['errors', 'too_long'], language_code, length=len(text), max=limit))
            return
        if editing == 'payment':
            # The owner's own link or requisites: they confirm each payment
            chat = await Chat.update_settings(chat['id'], {'access_provider': 'link', 'access_payment': text})
        else:
            chat = await Chat.update_settings(chat['id'], {'access_terms': None if text == '-' else text})
        _set_editing(params, None)
    await _render(params, chat, notice='✅ ' + _text(['toasts', 'saved'], language_code))


async def _connect_cryptobot(params: ControllerParams, chat: dict, token: str):
    """The token of the owner's Crypto Pay app: checked with getMe, kept encrypted, its message deleted."""
    language_code, message = params['language_code'], params['message']
    try:
        await bot.delete_message(message.chat.id, message.message_id)
    except (telegram_exceptions.TelegramBadRequest, telegram_exceptions.TelegramForbiddenError):
        pass
    try:
        label = await cryptobot.connect(token.strip())
    except cryptobot.ProviderError as e:
        cryptobot.log_error('the token did not work', e)
        await _render(params, chat, notice=_text(['errors', 'cryptobot_token'], language_code))
        return
    unsupported = [plan for plan in access.plans_of(chat) if not cryptobot.supports(plan['currency'])]
    chat = await Chat.update_settings(chat['id'], {
        'access_provider': cryptobot.NAME, 'access_secret': seal(token.strip()), 'access_provider_label': label})
    _set_editing(params, 'prices' if unsupported else None)
    await _render(params, chat, notice=_text(['toasts', 'cryptobot_connected'], language_code,
                                             label=html.escape(label)))


async def set_mode(params: ControllerParams):
    call, language_code = params['call'], params['language_code']
    chat = await _chat(params)
    if chat is None:
        return
    mode = params['state_data'].get('m')
    if mode not in access.MODES:
        return
    if mode == 'paid' and not Tariff.is_paid(await Chat.owner_tariff_id(chat['id'])):
        await notify(call, params['message'], _text(['errors', 'paid_only'], language_code), alert=True)
        return
    chat = await Chat.update_settings(chat['id'], {'access_mode': mode})
    # Paid entry without prices: straight to typing them
    _set_editing(params, 'prices' if mode == 'paid' and not access.plans_of(chat) else None)
    await notify(call, params['message'], _text(['toasts', {'off': 'off', 'request': 'request_on',
                                                            'paid': 'paid_on'}[mode]], language_code))
    await _render(params, chat)


async def edit(params: ControllerParams):
    chat = await _chat(params)
    if chat is None:
        return
    field = params['state_data'].get('f')
    _set_editing(params, field if field in EDITABLE else None)
    await params['call'].answer()
    await _render(params, chat)


async def cancel(params: ControllerParams):
    chat = await _chat(params)
    if chat is None:
        return
    _set_editing(params, None)
    await params['call'].answer()
    await _render(params, chat)


async def post(params: ControllerParams):
    """A message in the group with a button to the group's page in the bot, pinned if the bot may pin."""
    call, language_code = params['call'], params['language_code']
    chat = await _chat(params)
    if chat is None:
        return
    # The members read it in the group: in the owner's language, the group's most likely one
    markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(
        text=localization.get_message(['access', 'group_post', 'button'], language_code),
        url=access.join_link(chat['id']))]])
    try:
        sent = await bot.send_message(int(chat['service_id']), localization.get_message(
            ['access', 'group_post', 'text'], language_code), reply_markup=markup)
    except (telegram_exceptions.TelegramBadRequest, telegram_exceptions.TelegramForbiddenError) as e:
        logger.warning('Cannot post the way in to a group', chat['service_id'], e)
        await notify(call, params['message'], _text(['toasts', 'post_failed'], language_code), alert=True)
        return
    try:
        await bot.pin_chat_message(int(chat['service_id']), sent.message_id, disable_notification=True)
        toast = 'posted'
    except (telegram_exceptions.TelegramBadRequest, telegram_exceptions.TelegramForbiddenError):
        toast = 'posted_unpinned'
    await notify(call, params['message'], _text(['toasts', toast], language_code), alert=toast != 'posted')


async def requests(params: ControllerParams):
    """The requests waiting for an answer, again, below the page: one message each, with its buttons."""
    call, language_code = params['call'], params['language_code']
    chat = await _chat(params)
    if chat is None:
        return
    waiting = await Requests.pending(chat['id'])
    if not waiting:
        await notify(call, params['message'], _text(['toasts', 'no_requests'], language_code))
        return
    await notify(call, params['message'], _text(['toasts', 'requests_sent'], language_code))
    named = {**chat, 'name': await Chat.name_of(chat)}
    for request in waiting:
        await send_request(named, request, only_to=params['message'].chat.id)
