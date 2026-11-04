"""Tariffs and money: the free group, the limit on groups, changing a tariff, funding, the promised months."""
import datetime

from tests.bench import Bench, person

OWNER = person(501, 'owner', 'ru')
GROUP_1, GROUP_2, GROUP_3 = -1001000000001, -1001000000002, -1001000000003


async def _balance(bench: Bench, user_id: int, currency_code: str) -> int:
    [row] = await bench.sql(
        'SELECT balance FROM user_balances WHERE user_id = $1 AND currency_code = $2', user_id, currency_code)
    return row['balance']


async def _subscription(bench: Bench, user_id: int) -> dict:
    [row] = await bench.sql('SELECT * FROM user_tariff_connections WHERE user_id = $1', user_id)
    return row


def _days_from_now(moment: datetime.datetime) -> float:
    return (moment - datetime.datetime.now()).total_seconds() / 86400


async def test_new_user_on_free_tariff(bench: Bench):
    """a new user is on the free tariff, paying in the currency of their language, with no trial yet"""
    ru = await bench.owner(OWNER)
    en = await bench.owner(person(502, 'john', 'en'))
    for user, currency_code in ((ru, 'rub'), (en, 'usd')):
        subscription = await _subscription(bench, user['id'])
        assert subscription['tariff_id'] == 0
        assert subscription['payment_currency_code'] == currency_code, subscription
        assert subscription['trial_was_activated'] is False


async def test_free_tariff_one_group(bench: Bench):
    """the free tariff moderates one group: a second one is refused"""
    from pkg.service.chat import Chat

    owner = await bench.owner(OWNER)
    await bench.group(GROUP_1, owner)

    bench.group_in_telegram(GROUP_2, owner)
    result = await Chat.add(GROUP_2, OWNER['id'])
    assert result == {'error': 'subscription_limit_violation'}, result


async def test_trial_once(bench: Bench):
    """the menu starts the 15-day trial of tariff 1 once, and never again"""
    from pkg.service.tariff import Tariff

    owner = await bench.owner(OWNER)
    first = await Tariff.activate_trial(await Tariff.user_tariff_info(owner['id']))
    assert first['tariff_id'] == 1
    assert 14.9 < _days_from_now(first['end_date']) <= 15

    assert await Tariff.activate_trial(await Tariff.user_tariff_info(owner['id'])) is None


async def test_change_needs_balance(bench: Bench):
    """a paid tariff without the money on the balance is refused and nothing changes"""
    from pkg.service.tariff import Tariff

    owner = await bench.owner(OWNER)
    await Tariff.add_amount(owner['id'], 29999, 'rub')
    assert await Tariff.change(owner['id'], 1) == {'error': 'not_enough_balance'}
    assert (await _subscription(bench, owner['id']))['tariff_id'] == 0
    assert await _balance(bench, owner['id'], 'rub') == 29999


async def test_change_from_free_charges_full_price(bench: Bench):
    """from the free tariff a paid one costs its full monthly price and runs 30 days"""
    from pkg.service.tariff import Tariff

    owner = await bench.owner(OWNER)
    await Tariff.add_amount(owner['id'], 50000, 'rub')
    result = await Tariff.change(owner['id'], 1)
    assert result['tariff_id'] == 1, result
    assert await _balance(bench, owner['id'], 'rub') == 50000 - 30000
    assert 29.9 < _days_from_now(result['end_date']) <= 30


async def test_upgrade_charges_the_difference(bench: Bench):
    """an upgrade mid-month charges the new price for the days left minus the old one, the current day again"""
    from pkg.service.tariff import Tariff

    owner = await bench.owner(OWNER)
    await Tariff.add_amount(owner['id'], 200000, 'rub')
    await Tariff.change(owner['id'], 1)  # 300 ₽ for 30 days
    end_date = datetime.datetime.now() + datetime.timedelta(days=15, hours=1)
    await bench.sql('UPDATE user_tariff_connections SET end_date = $1 WHERE user_id = $2', end_date, owner['id'])
    before = await _balance(bench, owner['id'], 'rub')

    result = await Tariff.change(owner['id'], 2)  # 1000 ₽ for 30 days
    # 15 days left: 15/30 of 1000 ₽ for the new one, 14/30 of 300 ₽ back for the old one
    assert before - await _balance(bench, owner['id'], 'rub') == int(15 / 30 * 100000 - 14 / 30 * 30000)
    assert result['end_date'] == end_date, 'the period does not move'


async def test_downgrade_to_free_drops_extra_groups(bench: Bench):
    """back on the free tariff only the first group stays moderated, the others are disabled"""
    from pkg.service.tariff import Tariff

    owner = await bench.owner(OWNER)
    await Tariff.change(owner['id'], 2, force=True)
    await Tariff.prolong(owner['id'], 30)
    for group in (GROUP_1, GROUP_2, GROUP_3):
        await bench.group(group, owner)

    await Tariff.change(owner['id'], 0, force=True)
    rows = await bench.sql('SELECT service_id, disabled FROM moderated_chats ORDER BY id')
    assert [(row['service_id'], row['disabled']) for row in rows] == [
        (str(GROUP_1), False), (str(GROUP_2), True), (str(GROUP_3), True)], rows


async def test_promised_month(bench: Bench):
    """the promised free month (as for #337): tariff 1 for 30 days from today, the balance untouched"""
    from pkg.service.tariff import Tariff

    owner = await bench.owner(OWNER)
    await Tariff.add_amount(owner['id'], 1000, 'rub')
    await Tariff.change(owner['id'], 1, force=True)
    end_date = await Tariff.prolong(owner['id'], 30)

    subscription = await _subscription(bench, owner['id'])
    assert subscription['tariff_id'] == 1
    assert 29.9 < _days_from_now(end_date) <= 30, end_date
    assert await _balance(bench, owner['id'], 'rub') == 1000


async def test_funding_credits_once(bench: Bench):
    """a payment credits the balance, is written to the history and tells the user; the same payment twice
    credits once"""
    from pkg.service.payment import BalanceHandler

    owner = await bench.owner(OWNER)
    payment = {'service': 'robokassa', 'user_id': owner['id'], 'amount': 75000, 'currency': 'rub', 'id': 'inv-1'}
    await BalanceHandler.funding(payment)
    await BalanceHandler.funding(payment)

    assert await _balance(bench, owner['id'], 'rub') == 75000
    assert len(await bench.sql('SELECT id FROM payments_history')) == 1
    assert len(bench.telegram.sent_to(OWNER['id'])) == 1


async def test_funding_wrong_signature(bench: Bench):
    """a payment with a bad signature credits nothing and the user is told"""
    from pkg.service.payment import BalanceHandler

    owner = await bench.owner(OWNER)
    await BalanceHandler.funding({'service': 'robokassa', 'user_id': owner['id'], 'amount': 75000,
                                  'currency': 'rub', 'error': 'wrong_signature'})
    assert await _balance(bench, owner['id'], 'rub') == 0
    assert len(bench.telegram.sent_to(OWNER['id'])) == 1


async def test_prolong_expired_from_today(bench: Bench):
    """days given to a subscription that has ended count from today, not from the past end date"""
    from pkg.service.tariff import Tariff

    owner = await bench.owner(OWNER)
    await Tariff.change(owner['id'], 1, force=True)
    await bench.sql("UPDATE user_tariff_connections SET end_date = LOCALTIMESTAMP - interval '10 days'")
    assert 6.9 < _days_from_now(await Tariff.prolong(owner['id'], 7)) <= 7


async def test_referrer_rewarded(bench: Bench):
    """when an invited user pays, the one who invited them gets half the days the payment buys"""
    from pkg.service.payment import BalanceHandler
    from pkg.service.user import User

    referrer = await bench.owner(OWNER)
    invited = (await User.register(502, 'ru', {'referral': str(OWNER['id'])}))['user']
    assert invited['ref_id'] == referrer['id']

    # 300 ₽ buys a month of tariff 1, so the referrer, moved from the free tariff to it, gets 15 days
    await BalanceHandler.funding({'service': 'robokassa', 'user_id': invited['id'], 'amount': 30000,
                                  'currency': 'rub', 'id': 'inv-2'})
    subscription = await _subscription(bench, referrer['id'])
    assert subscription['tariff_id'] == 1
    assert 14.9 < _days_from_now(subscription['end_date']) <= 15, subscription['end_date']
    assert len(bench.telegram.sent_to(OWNER['id'])) == 1, 'the referrer is told'


async def test_test_payment_only_for_admins_in_production(bench: Bench):
    """in production a Robokassa test payment (IsTest=1) credits nothing unless the user is a bot admin"""
    from pkg.config.config import environment
    from pkg.service.payment import BalanceHandler

    user = await bench.owner(OWNER)
    admin = await bench.owner(person(1, 'admin', 'ru'))
    await bench.sql('UPDATE users SET is_admin = TRUE WHERE id = $1', admin['id'])

    environment['ENVIRONMENT'] = 'production'
    try:
        for who, invoice in ((user, 'inv-3'), (admin, 'inv-4')):
            await BalanceHandler.funding({'service': 'robokassa', 'user_id': who['id'], 'amount': 100000,
                                          'currency': 'rub', 'id': invoice, 'is_test': True})
    finally:
        environment['ENVIRONMENT'] = 'development'

    assert await _balance(bench, user['id'], 'rub') == 0
    assert await _balance(bench, admin['id'], 'rub') == 100000


async def test_hourly_round_disables_expired(bench: Bench):
    """the hourly round moves an expired paid subscription without money back to the free tariff and tells the
    owner"""
    from pkg.background.async_tasks.subscription_handler import subscription_handler_round
    from pkg.service.tariff import Tariff

    owner = await bench.owner(OWNER)
    await Tariff.change(owner['id'], 1, force=True)
    await bench.sql("UPDATE user_tariff_connections SET end_date = LOCALTIMESTAMP - interval '1 hour'")
    await subscription_handler_round()

    assert (await _subscription(bench, owner['id']))['tariff_id'] == 0
    assert len(bench.telegram.sent_to(OWNER['id'])) == 1


async def test_hourly_round_survives_failure(bench: Bench):
    """a failing round (the database away for a moment) is logged and does not end the hourly task"""
    import os
    from unittest import mock

    from pkg.background.async_tasks import subscription_handler

    async def unreachable():
        raise ConnectionError('database unreachable')
        yield  # pragma: no cover

    os.environ['ENVIRONMENT'] = 'production'  # the logger raises errors in development
    try:
        with mock.patch.object(subscription_handler.Tariff, 'process_all_subscription_validity', unreachable):
            await subscription_handler.subscription_handler_round()
    finally:
        os.environ['ENVIRONMENT'] = 'development'
