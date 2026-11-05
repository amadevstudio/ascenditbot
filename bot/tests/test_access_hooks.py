"""Paid entry through YooMoney and Tribute, which tell the bot about payments at /hook/<provider>/<key>: the
owner connects them, a signed notification opens access once, a wrong signature changes nothing."""
import base64
import datetime
import hashlib
import hmac
import json
import urllib.parse

from tests.bench import Bench
from tests.test_access import BUYER, OWNER, PLANS, _buttons, _last_to, _press, _scene

WALLET = '410011234567890'
SECRET = 'yoomoney-secret-1'
API_KEY = 'tribute-key-1'
PRODUCTS = [{'id': 11, 'name': 'Неделя', 'link': 'https://t.me/tribute/app?startapp=p11', 'status': 'approved'},
            {'id': 12, 'name': 'Месяц', 'link': 'https://t.me/tribute/app?startapp=p12', 'status': 'approved'}]


def _hooks_on():
    from pkg.service.access_providers import tribute, yoomoney

    async def post(form):
        return f"https://yoomoney.ru/transfer/quickpay?requestId={form['label']}"

    async def request(api_key, path, params=None):
        if api_key != API_KEY:
            raise tribute.ProviderError('401')
        return {'rows': PRODUCTS, 'meta': {'total': 2}}

    yoomoney._post = post
    tribute._request = request


def _signed(params: dict, secret: str = SECRET) -> dict:
    line = '&'.join(f"{k}={urllib.parse.quote(str(v), safe='')}" for k, v in sorted(params.items()))
    return {**params, 'sign': hmac.new(secret.encode(), line.encode(), hashlib.sha256).hexdigest()}


def _transfer(label: str, paid: str, test: bool = False) -> dict:
    params = {'notification_type': 'card-incoming', 'operation_id': f'op-{label}', 'amount': paid,
              'withdraw_amount': paid, 'currency': '643', 'datetime': '2026-11-05T10:00:00Z', 'sender': '',
              'codepro': 'false', 'label': label, 'unaccepted': 'false'}
    if test:
        params['test_notification'] = 'true'
    return _signed(params)


async def _yoomoney_scene(bench: Bench) -> dict:
    from pkg.service.access_providers import hook_key
    from pkg.service.secret_box import seal

    return await _scene(bench, access_mode='paid', access_plans=PLANS, access_provider='yoomoney',
                        access_secret=seal(json.dumps({'wallet': WALLET, 'secret': SECRET})),
                        access_hook_key=hook_key('yoomoney', WALLET), access_provider_label='4100…7890')


async def test_owner_connects_yoomoney(bench: Bench):
    """YooMoney: the wallet, then the address to paste and the secret (deleted); a signed test is confirmed"""
    from pkg.service.access_hooks import on_yoomoney
    from pkg.service.access_providers import hook_key

    _hooks_on()
    chat = await _scene(bench, access_mode='paid', access_plans=PLANS)
    await bench.private_message(OWNER, f'/start chat_{chat["id"]}')
    await bench.tap(OWNER, '{"tp":"chat_access"}')
    await bench.tap(OWNER, '{"tp":"acc_edit","f":"payment"}')
    await bench.tap(OWNER, _press(_last_to(bench, OWNER), 'ЮMoney'))
    await bench.private_message(OWNER, '1234')
    assert 'не номер кошелька' in _last_to(bench, OWNER).text
    await bench.private_message(OWNER, '4100 1123 4567 890')
    key = hook_key('yoomoney', WALLET)
    prompt = _last_to(bench, OWNER).text
    assert f'https://ascendit.wrkt.ru/hook/yoomoney/{key}' in prompt and 'Показать секрет' in prompt, prompt
    await bench.private_message(OWNER, SECRET)
    assert 'ЮMoney подключён' in _last_to(bench, OWNER).text
    [row] = await bench.sql('SELECT access_provider, access_hook_key, access_provider_label FROM moderated_chats')
    assert row == {'access_provider': 'yoomoney', 'access_hook_key': key, 'access_provider_label': '4100…7890'}

    bench.telegram.calls.clear()
    assert await on_yoomoney(key, _signed({'label': '', 'test_notification': 'true'}, 'wrong')) == 400
    assert await on_yoomoney(key, _transfer('', '100.00', test=True)) == 200
    assert 'ЮMoney достучался до бота' in _last_to(bench, OWNER).text


async def test_member_pays_by_yoomoney(bench: Bench):
    """a term → a YooMoney payment page; the signed transfer with its label opens access once; less money does
    not open it, the owner hears"""
    from pkg.service.access_hooks import on_yoomoney
    from pkg.service.access_providers import hook_key

    _hooks_on()
    chat = await _yoomoney_scene(bench)
    key = hook_key('yoomoney', WALLET)
    await bench.private_message(BUYER, f'/start j_{chat["id"]}')
    await bench.tap(BUYER, _press(_last_to(bench, BUYER), '30 дней'))
    screen = _last_to(bench, BUYER)
    assert 'ЮMoney (картой)' in screen.text
    assert [b['url'] for b in _buttons(screen) if b['url']] == ['https://yoomoney.ru/transfer/quickpay?requestId=r1']

    assert await on_yoomoney(key, _transfer('r1', '500.00')) == 200
    assert not await bench.sql('SELECT 1 FROM allowed_users')
    assert 'а цена 1 000 ₽' in _last_to(bench, OWNER).text

    assert await on_yoomoney(key, _transfer('r1', '1000.00')) == 200
    assert await on_yoomoney(key, _transfer('r1', '1000.00')) == 200
    [entry] = await bench.sql('SELECT expires_at FROM allowed_users')
    assert datetime.timedelta(days=29) < entry['expires_at'] - datetime.datetime.now() <= datetime.timedelta(days=30)
    paid = [c for c in bench.telegram.calls_of('sendMessage') if int(c.chat_id) == BUYER['id'] and 'Оплата получена' in c.text]
    assert len(paid) == 1
    assert await on_yoomoney(key, {**_transfer('r1', '1000.00'), 'sign': '0' * 64}) == 400


async def test_yoomoney_paid_late_still_opens_access(bench: Bench):
    """the payment page of a term replaced by another, or of a request the bot stopped waiting for, has no end
    in YooMoney: paid late, it opens access all the same"""
    from pkg.service.access_hooks import on_yoomoney
    from pkg.service.access_providers import hook_key

    _hooks_on()
    chat = await _yoomoney_scene(bench)
    key = hook_key('yoomoney', WALLET)
    await bench.private_message(BUYER, f'/start j_{chat["id"]}')
    await bench.tap(BUYER, _press(_last_to(bench, BUYER), '7 дней'))
    await bench.tap(BUYER, _press(_last_to(bench, BUYER), 'Другой срок'))
    assert await on_yoomoney(key, _transfer('r1', '300.00')) == 200
    [entry] = await bench.sql('SELECT expires_at FROM allowed_users')
    assert datetime.timedelta(days=6) < entry['expires_at'] - datetime.datetime.now() <= datetime.timedelta(days=7)

    await bench.sql("DELETE FROM allowed_users")
    await bench.private_message(BUYER, f'/start j_{chat["id"]}')
    await bench.tap(BUYER, _press(_last_to(bench, BUYER), '30 дней'))
    await bench.sql("UPDATE access_requests SET status = 'expired' WHERE id = 2")
    assert await on_yoomoney(key, _transfer('r2', '1000.00')) == 200
    assert await bench.sql('SELECT 1 FROM allowed_users')


async def test_owner_connects_tribute_and_maps_terms(bench: Bench):
    """Tribute: the key (deleted, checked by listing products), a product for each term, then the webhook
    address"""
    from pkg.service.access_providers import hook_key

    _hooks_on()
    chat = await _scene(bench, access_mode='paid', access_plans=PLANS)
    await bench.private_message(OWNER, f'/start chat_{chat["id"]}')
    await bench.tap(OWNER, '{"tp":"chat_access"}')
    await bench.tap(OWNER, '{"tp":"acc_edit","f":"payment"}')
    await bench.tap(OWNER, _press(_last_to(bench, OWNER), 'Tribute'))
    assert '7 дней – 300 ₽, 30 дней – 1 000 ₽' in _last_to(bench, OWNER).text
    await bench.private_message(OWNER, 'wrong')
    assert 'не принял ключ' in _last_to(bench, OWNER).text
    await bench.private_message(OWNER, API_KEY)
    screen = _last_to(bench, OWNER)
    assert 'на <b>7 дней – 300 ₽</b>' in screen.text and 'Неделя' in [b['text'] for b in _buttons(screen)]
    await bench.tap(OWNER, _press(screen, 'Неделя'))
    screen = _last_to(bench, OWNER)
    assert 'на <b>30 дней – 1 000 ₽</b>' in screen.text
    await bench.tap(OWNER, _press(screen, 'Месяц'))
    done = _last_to(bench, OWNER).text
    assert f'https://ascendit.wrkt.ru/hook/tribute/{hook_key("tribute", API_KEY)}' in done, done
    [row] = await bench.sql('SELECT access_plans FROM moderated_chats')
    assert [(p['days'], p['product_id']) for p in json.loads(row['access_plans'])] == [(7, 11), (30, 12)]


async def test_tribute_purchase_opens_access_and_a_refund_asks_the_owner(bench: Bench):
    """a signed purchase of the product of 30 days opens access for 30 days, once; a bad signature is refused;
    a refund offers the owner to take the access away"""
    from pkg.service.access_hooks import on_tribute
    from pkg.service.access_providers import hook_key
    from pkg.service.secret_box import seal

    _hooks_on()
    plans = json.dumps([{'days': 30, 'amount': '1000', 'currency': 'RUB', 'product_id': 12, 'product_name': 'Месяц',
                         'url': 'https://t.me/tribute/app?startapp=p12'}])
    chat = await _scene(bench, access_mode='paid', access_plans=plans, access_provider='tribute',
                        access_secret=seal(json.dumps({'api_key': API_KEY})),
                        access_hook_key=hook_key('tribute', API_KEY), access_provider_label='Tribute')
    key = hook_key('tribute', API_KEY)

    await bench.private_message(BUYER, f'/start j_{chat["id"]}')
    await bench.tap(BUYER, _press(_last_to(bench, BUYER), '30 дней'))
    screen = _last_to(bench, BUYER)
    assert [b['url'] for b in _buttons(screen) if b['url']] == ['https://t.me/tribute/app?startapp=p12']

    body = json.dumps({'name': 'new_digital_product', 'created_at': '', 'sent_at': '', 'payload': {
        'product_id': 12, 'amount': 1000, 'currency': 'rub', 'purchase_id': 77, 'transaction_id': 5,
        'telegram_user_id': BUYER['id'], 'telegram_username': 'buyer'}}).encode()
    digest = hmac.new(API_KEY.encode(), body, hashlib.sha256).digest()
    assert await on_tribute(key, body, 'bad') == 401
    assert await on_tribute(key, body, digest.hex()) == 200
    assert await on_tribute(key, body, base64.b64encode(digest).decode()) == 200
    [entry] = await bench.sql('SELECT user_service_id, expires_at FROM allowed_users')
    assert entry['user_service_id'] == str(BUYER['id'])
    assert len([c for c in bench.telegram.calls_of('sendMessage')
                if int(c.chat_id) == BUYER['id'] and 'Оплата получена' in c.text]) == 1

    refund = json.dumps({'name': 'digital_product_refunded', 'payload': {
        'product_id': 12, 'purchase_id': 77, 'amount': 1000, 'currency': 'rub', 'refund_reason': 'telegram_refund',
        'telegram_user_id': BUYER['id']}}).encode()
    assert await on_tribute(key, refund, hmac.new(API_KEY.encode(), refund, hashlib.sha256).hexdigest()) == 200
    alert = _last_to(bench, OWNER)
    assert 'Tribute вернул оплату' in alert.text
    await bench.tap(OWNER, _press(alert, 'Убрать доступ'))
    assert not await bench.sql('SELECT 1 FROM allowed_users')
