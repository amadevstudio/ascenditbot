"""Payment through a provider that confirms it (pkg/service/access_providers): the invoice for the term a member
picked, and checking the invoices waited for, every POLL_SECONDS and when the member taps "Check". A paid one
opens access on its own; the member and the managers hear it."""
import asyncio
import datetime

from pkg.service import access
from pkg.service.access import Requests
from pkg.service.access_providers import cryptobot
from pkg.service.allowed_user import full_name
from pkg.service.secret_box import unseal
from pkg.repository import access_repository
from pkg.system.logger import logger

PROVIDERS = {cryptobot.NAME: cryptobot}
POLL_SECONDS = 20
# An invoice is waited for this long, then the request expires (the invoice itself lives an hour)
WAIT = datetime.timedelta(hours=2)
# An unpaid invoice of the same term is shown again rather than a new one made, while it has this long to live
REUSE = datetime.timedelta(minutes=45)


def provider_of(chat: dict):
    return PROVIDERS.get(chat.get('access_provider') or '')


async def start(chat: dict, user, language_code: str | None, plan: dict) -> dict:
    """The member's request with an invoice to pay: {'request'} or {'error': 'unavailable' | 'provider'}."""
    provider = provider_of(chat)
    token = unseal(chat.get('access_secret'))
    if provider is None or token is None:
        return {'error': 'unavailable'}

    latest = await Requests.latest(chat['id'], str(user.id))
    if latest is not None and latest['status'] == 'pending':
        same = (latest['kind'] == 'paid_auto' and latest['days'] == plan['days'] and latest['pay_url']
                and latest['created_at'] > datetime.datetime.now() - REUSE)
        if same:
            return {'request': latest}
        # Another term, or an old invoice: the new one replaces it
        await Requests.decide(latest['id'], 'cancelled', None)

    request = await Requests.create({
        'moderated_chat_id': chat['id'], 'user_service_id': str(user.id), 'nickname': user.username,
        'display_name': full_name(user), 'language_code': language_code, 'kind': 'paid_auto',
        'days': plan['days'], 'amount': plan['amount'], 'currency': plan['currency'], 'provider': provider.NAME})
    if request is None:
        return {'error': 'provider'}
    description = f"{chat.get('name') or ''}: {access.plan_text(plan, language_code)}"
    try:
        invoice = await provider.create_invoice(token, plan, description, f"r{request['id']}")
    except cryptobot.ProviderError as e:
        provider.log_error('cannot create an invoice', e)
        await Requests.decide(request['id'], 'cancelled', None)
        return {'error': 'provider'}
    request = await Requests.update(request['id'], {'external_id': invoice['external_id'], 'pay_url': invoice['url']})
    return {'request': request}


async def settle(request: dict, status: str) -> dict | None:
    """A provider's answer about one request: paid opens access (once), expired closes the request. The entry
    of the whitelist when access opened."""
    if status == 'expired' or (status != 'paid' and request['created_at'] < datetime.datetime.now() - WAIT):
        await Requests.decide(request['id'], 'expired', None)
        return None
    if status != 'paid':
        return None
    if await Requests.decide(request['id'], 'approved', request['provider']) is None:
        return None  # settled already

    from pkg.controller.routers.quick_actions_router import lift_restriction
    from pkg.service.access_messages import tell_paid
    from pkg.service.chat import Chat

    entry = await access.grant(request['moderated_chat_id'], request['user_service_id'], request['nickname'],
                               request['display_name'], request['days'] or 0)
    chat = await Chat.find(request['moderated_chat_id'])
    if chat is None:
        return entry
    await lift_restriction(int(chat['service_id']), int(request['user_service_id']))
    chat = {**chat, 'name': await Chat.name_of(chat)}
    chat_info = await Chat.load_info(str(chat['service_id']))
    await tell_paid(chat, request, entry, chat_info.get('nickname'))
    return entry


async def check(requests: list[dict]) -> dict[int, dict | None]:
    """Asks the providers about these requests (with their groups' settings) and settles them; the whitelist
    entries of those paid, by request id."""
    settled = {}
    by_token: dict[tuple[str, str], list[dict]] = {}
    for request in requests:
        token = unseal(request.get('access_secret'))
        if token is None or request['provider'] not in PROVIDERS:
            await settle(request, 'expired' if request['created_at'] < datetime.datetime.now() - WAIT else 'active')
            continue
        by_token.setdefault((request['provider'], token), []).append(request)
    for (name, token), group in by_token.items():
        try:
            found = await PROVIDERS[name].statuses(token, [request['external_id'] for request in group])
        except cryptobot.ProviderError as e:
            PROVIDERS[name].log_error('cannot check invoices', e)
            continue
        for request in group:
            entry = await settle(request, found.get(request['external_id'], 'active'))
            if entry is not None:
                settled[request['id']] = entry
    return settled


async def poll_round():
    await check(await access_repository.waiting_payments(tuple(PROVIDERS)))


async def poll_forever():
    while True:
        try:
            await poll_round()
        except Exception as e:
            logger.error('Access payments: the round failed', e)
        await asyncio.sleep(POLL_SECONDS)
