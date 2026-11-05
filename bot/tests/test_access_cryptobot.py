"""Paid entry through CryptoBot (Crypto Pay): the owner connects their app by its token, a member gets an invoice
for the term they pick, access opens by itself once it is paid (the round of checks, or "Check")."""
import datetime
import json

from tests.bench import Bench
from tests.test_access import BUYER, GROUP, OWNER, PLANS, _buttons, _last_to, _press, _scene


class FakeCryptoPay:
    """The Crypto Pay API of one app ("Shop", token "good"): invoices kept here, statuses set by the test."""

    def __init__(self):
        self.invoices: dict[str, dict] = {}
        self.calls: list[tuple[str, dict]] = []
        self.down = False

    async def request(self, token: str, method: str, params: dict | None = None):
        from pkg.service.access_providers.cryptobot import ProviderError

        params = params or {}
        self.calls.append((method, params))
        if self.down:
            raise ProviderError(f'{method}: down')
        if token != 'good':
            raise ProviderError(f'{method}: UNAUTHORIZED')
        if method == 'getMe':
            return {'app_id': 1, 'name': 'Shop', 'payment_processing_bot_username': 'CryptoBot'}
        if method == 'createInvoice':
            invoice_id = str(len(self.invoices) + 100)
            self.invoices[invoice_id] = {'invoice_id': int(invoice_id), 'status': 'active', **params,
                                         'bot_invoice_url': f'https://t.me/CryptoBot?start={invoice_id}'}
            return self.invoices[invoice_id]
        if method == 'getInvoices':
            wanted = params['invoice_ids'].split(',')
            return {'items': [self.invoices[i] for i in wanted if i in self.invoices]}
        raise AssertionError(method)

    def pay(self, invoice_id: str):
        self.invoices[invoice_id]['status'] = 'paid'


def _fake() -> FakeCryptoPay:
    from pkg.service.access_providers import cryptobot

    fake = FakeCryptoPay()
    cryptobot._request = fake.request
    return fake


async def _cryptobot_scene(bench: Bench) -> dict:
    from pkg.service.secret_box import seal

    return await _scene(bench, access_mode='paid', access_plans=PLANS, access_provider='cryptobot',
                        access_secret=seal('good'), access_provider_label='Shop')


async def test_owner_connects_cryptobot(bench: Bench):
    """the way to pay: CryptoBot; a wrong token is refused, a good one is kept encrypted; both messages deleted"""
    from pkg.service.secret_box import unseal

    fake = _fake()
    chat = await _scene(bench, access_mode='paid', access_plans=PLANS)
    await bench.private_message(OWNER, f'/start chat_{chat["id"]}')
    await bench.tap(OWNER, '{"tp":"chat_access"}')
    await bench.tap(OWNER, '{"tp":"acc_edit","f":"payment"}')
    page = _last_to(bench, OWNER)
    assert 'Шаг 2 из 2' in page.text and 'CryptoBot' in page.text, page.text
    await bench.tap(OWNER, _press(page, 'CryptoBot'))
    assert 'Create App' in _last_to(bench, OWNER).text

    await bench.private_message(OWNER, 'bad-token')
    assert 'не принял токен' in _last_to(bench, OWNER).text
    await bench.private_message(OWNER, 'good')
    assert len(bench.telegram.calls_of('deleteMessage')) >= 2
    page = _last_to(bench, OWNER)
    assert 'CryptoBot подключён: приложение "Shop"' in page.text and 'приложение "Shop"' in page.text, page.text
    [row] = await bench.sql('SELECT access_provider, access_secret, access_provider_label FROM moderated_chats')
    assert row['access_provider'] == 'cryptobot' and row['access_secret'] != 'good'
    assert unseal(row['access_secret']) == 'good' and row['access_provider_label'] == 'Shop'
    assert ('getMe', {}) in fake.calls


async def test_member_pays_through_cryptobot_and_access_opens_by_itself(bench: Bench):
    """a term → an invoice (the same one on a second tap); "Check" before paying says wait; paid → the round opens
    access for 30 days once, the member and the owner hear it"""
    from pkg.service.access_payments import poll_round

    fake = _fake()
    chat = await _cryptobot_scene(bench)
    await bench.private_message(BUYER, f'/start j_{chat["id"]}')
    page = _last_to(bench, BUYER)
    await bench.tap(BUYER, _press(page, '30 дней'))
    screen = _last_to(bench, BUYER)
    assert 'Доступ откроется сам' in screen.text, screen.text
    pay = [b['url'] for b in _buttons(screen) if b['url']]
    assert pay == ['https://t.me/CryptoBot?start=100'], _buttons(screen)
    [(method, params)] = [call for call in fake.calls if call[0] == 'createInvoice']
    assert params['currency_type'] == 'fiat' and params['fiat'] == 'RUB' and params['amount'] == '1000'

    await bench.tap(BUYER, _press(page, '30 дней'))
    assert len([call for call in fake.calls if call[0] == 'createInvoice']) == 1

    await bench.tap(BUYER, _press(screen, 'Проверить оплату'))
    assert 'пока не пришла' in bench.telegram.calls_of('answerCallbackQuery')[-1].text
    assert not await bench.sql('SELECT 1 FROM allowed_users')

    fake.pay('100')
    await poll_round()
    await poll_round()
    [entry] = await bench.sql('SELECT user_service_id, expires_at FROM allowed_users')
    assert entry['user_service_id'] == str(BUYER['id'])
    assert datetime.timedelta(days=29) < entry['expires_at'] - datetime.datetime.now() <= datetime.timedelta(days=30)
    paid_texts = [call.text for call in bench.telegram.calls_of('sendMessage') if int(call.chat_id) == BUYER['id']
                  and 'Оплата получена' in call.text]
    assert len(paid_texts) == 1, paid_texts
    owner_texts = [call.text for call in bench.telegram.calls_of('sendMessage') if int(call.chat_id) == OWNER['id']]
    assert any('Оплата через CryptoBot' in text and 'Доступ открыт до' in text for text in owner_texts), owner_texts
    [request] = await bench.sql('SELECT status, decided_by FROM access_requests')
    assert request == {'status': 'approved', 'decided_by': 'cryptobot'}


async def test_check_button_opens_access_at_once(bench: Bench):
    """paid, then "Check": access opens without waiting for the round"""
    fake = _fake()
    chat = await _cryptobot_scene(bench)
    await bench.private_message(BUYER, f'/start j_{chat["id"]}')
    await bench.tap(BUYER, _press(_last_to(bench, BUYER), '7 дней'))
    screen = _last_to(bench, BUYER)
    fake.pay('100')
    await bench.tap(BUYER, _press(screen, 'Проверить оплату'))
    assert await bench.sql('SELECT 1 FROM allowed_users')
    assert 'У вас есть доступ до' in _last_to(bench, BUYER).text


async def test_another_term_and_expired_invoices(bench: Bench):
    """"Another term" drops the invoice; an expired invoice closes its request; the page offers terms again"""
    from pkg.service.access_payments import poll_round

    fake = _fake()
    chat = await _cryptobot_scene(bench)
    await bench.private_message(BUYER, f'/start j_{chat["id"]}')
    await bench.tap(BUYER, _press(_last_to(bench, BUYER), '7 дней'))
    await bench.tap(BUYER, _press(_last_to(bench, BUYER), 'Другой срок'))
    page = _last_to(bench, BUYER)
    assert '30 дней – 1 000 ₽' in [b['text'] for b in _buttons(page)], page.text
    await bench.tap(BUYER, _press(page, '30 дней'))
    fake.invoices['101']['status'] = 'expired'
    await poll_round()
    statuses = [row['status'] for row in await bench.sql('SELECT status FROM access_requests ORDER BY id')]
    assert statuses == ['cancelled', 'expired'], statuses
    await bench.private_message(BUYER, f'/start j_{chat["id"]}')
    assert 'Выберите срок' in _last_to(bench, BUYER).text


async def test_cryptobot_down(bench: Bench):
    """CryptoBot does not answer: the member is told to try later, nothing is left waiting"""
    fake = _fake()
    chat = await _cryptobot_scene(bench)
    await bench.private_message(BUYER, f'/start j_{chat["id"]}')
    fake.down = True
    await bench.tap(BUYER, _press(_last_to(bench, BUYER), '7 дней'))
    assert 'не ответила' in bench.telegram.calls_of('answerCallbackQuery')[-1].text
    assert [row['status'] for row in await bench.sql('SELECT status FROM access_requests')] == ['cancelled']
