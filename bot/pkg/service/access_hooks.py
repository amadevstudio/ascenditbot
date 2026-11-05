"""What YooMoney and Tribute tell the bot (pkg/service/access_providers), at constants.hooks_url:

- POST /hook/yoomoney/<key>: a transfer to the owner's wallet (form fields), or the test from the settings page;
- POST /hook/tribute/<key>: a purchase of a digital product (JSON), or its refund.

The key finds the groups (moderated_chats.access_hook_key); the signature, checked with each one's
credentials, proves the call. Each returns the HTTP status to answer."""
import datetime
import html
import json

from aiohttp import web
from aiogram.types import InlineKeyboardMarkup

from lib.language import localization
from pkg.repository import access_repository, chat_repository
from pkg.service import access, access_payments
from pkg.service.access import Requests
from pkg.service.access_messages import _button, _send, request_member
from pkg.service.access_providers import tribute, yoomoney
from pkg.system.logger import logger

# A test notification is answered once a minute at most
_tested: dict[str, datetime.datetime] = {}


async def _tell_managers(chat: dict, key: list, markup_for=None, **kwargs):
    """Every manager of the group, in their language; `markup_for(language_code)` makes the buttons."""
    from pkg.service.chat import Chat

    chat_name = html.escape(await Chat.name_of(chat))
    for manager in await chat_repository.managers(chat['id']):
        language_code = manager['language_code']
        await _send(manager['service_id'], localization.get_message(
            ['access', 'hooks', *key], language_code, chat_name=chat_name, **kwargs),
            markup_for(language_code) if markup_for else None)


async def on_yoomoney(hook_key: str, params: dict) -> int:
    chats = [chat for chat in await chat_repository.by_hook_key(yoomoney.NAME, hook_key)
             if (found := access_payments.credentials(chat)) and yoomoney.verify(params, found.get('secret', ''))]
    if not chats:
        logger.warning('YooMoney: a notification not signed for any group', hook_key, params.get('operation_id'))
        return 400

    if str(params.get('test_notification', '')).lower() == 'true':
        now = datetime.datetime.now()
        if _tested.get(hook_key, now - datetime.timedelta(minutes=2)) < now - datetime.timedelta(minutes=1):
            _tested[hook_key] = now
            for chat in chats:
                await _tell_managers(chat, ['yoomoney_test'])
        return 200

    label = str(params.get('label') or '')
    request = await Requests.find(int(label[1:])) if label[:1] == 'r' and label[1:].isdigit() else None
    if request is None or request['provider'] != yoomoney.NAME \
            or request['moderated_chat_id'] not in {chat['id'] for chat in chats}:
        return 200  # another transfer to the wallet
    if request['status'] not in ('pending', 'cancelled', 'expired'):
        return 200  # settled already
    paid = yoomoney.paid_amount(params)
    if paid < request['amount']:
        chat = next(chat for chat in chats if chat['id'] == request['moderated_chat_id'])
        await _tell_managers(chat, ['yoomoney_short'], member=request_member(request),
                             paid=access.format_amount(paid, 'RUB'),
                             price=access.format_amount(request['amount'], 'RUB'))
        return 200
    await access_payments.settle(request, 'paid')
    return 200


async def on_tribute(hook_key: str, body: bytes, signature: str | None) -> int:
    chats = [chat for chat in await chat_repository.by_hook_key(tribute.NAME, hook_key)
             if (found := access_payments.credentials(chat)) and tribute.verify(body, signature, found['api_key'])]
    if not chats:
        logger.warning('Tribute: a webhook not signed for any group', hook_key)
        return 401
    try:
        event = json.loads(body)
        name, payload = event['name'], event.get('payload') or {}
    except (ValueError, KeyError, TypeError):
        return 400

    if name == 'new_digital_product':
        product_id = payload.get('product_id')
        found = [(chat, plan) for chat in chats for plan in access.plans_of(chat)
                 if plan.get('product_id') is not None and str(plan['product_id']) == str(product_id)]
        if not found:
            return 200  # a product of the owner's that is not a way into a group
        purchase = str(payload.get('purchase_id') or payload.get('transaction_id') or '')
        buyer = payload.get('telegram_user_id')
        for chat, plan in found:
            if not buyer:
                await _tell_managers(chat, ['tribute_no_buyer'], product=html.escape(plan.get('product_name') or ''))
                continue
            external_id = f'{chat["id"]}:{purchase}'
            if await access_repository.find_by_external(tribute.NAME, external_id) is not None:
                continue  # told already
            latest = await Requests.latest(chat['id'], str(buyer))
            if latest is not None and latest['status'] == 'pending':
                await Requests.decide(latest['id'], 'cancelled', None)
            request = await Requests.create({
                'moderated_chat_id': chat['id'], 'user_service_id': str(buyer),
                'nickname': payload.get('telegram_username'), 'display_name': None, 'language_code': None,
                'kind': 'paid_auto', 'days': plan['days'], 'amount': plan['amount'], 'currency': plan['currency'],
                'provider': tribute.NAME, 'external_id': external_id})
            if request is not None:
                await access_payments.settle(request, 'paid')
        return 200

    if name == 'digital_product_refunded':
        purchase = str(payload.get('purchase_id') or '')
        for chat in chats:
            request = await access_repository.find_by_external(tribute.NAME, f'{chat["id"]}:{purchase}')
            if request is None:
                continue
            # The owner decides: Tribute gave the money back, the bot offers to take the access away
            from pkg.service.member_alerts import save_token
            token = save_token({'c': chat['id'], 'u': request['user_service_id'], 'n': request['nickname'],
                                'name': request['display_name']})
            def markup_for(language_code: str | None, token=token) -> InlineKeyboardMarkup:
                return InlineKeyboardMarkup(inline_keyboard=[[_button(localization.get_message(
                    ['access', 'hooks', 'remove_access'], language_code), {'tp': 'qu', 'k': token})]])
            await _tell_managers(chat, ['tribute_refund'], markup_for, member=request_member(request))
        return 200

    return 200


# The routes of the payment server (lib/payment/payment.py)

async def _yoomoney_route(request: web.Request) -> web.Response:
    params = {key: str(value) for key, value in (await request.post()).items()}
    status = await on_yoomoney(request.match_info['key'], params)
    return web.Response(status=status, text='ok' if status == 200 else 'bad request')


async def _tribute_route(request: web.Request) -> web.Response:
    status = await on_tribute(request.match_info['key'], await request.read(), request.headers.get('trbt-signature'))
    return web.json_response({'status': 'ok'} if status == 200 else {'error': status}, status=status)


def routes() -> list[web.RouteDef]:
    return [web.post('/hook/yoomoney/{key}', _yoomoney_route), web.post('/hook/tribute/{key}', _tribute_route)]
