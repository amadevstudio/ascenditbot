"""Product Hunt attribution stays separate from referrals, participant payments and trial access."""
import json

from tests.bench import Bench, person

OWNER = person(99101, 'ph-owner', 'ru')
GROUP = -100199101


async def test_start_sources_preserve_referral_chat_and_join_links(bench: Bench):
    """only the allowlisted PH marker is a source; legacy deep links keep their own meaning"""
    from pkg.service.user import User

    assert User.analyze_initial_data('/start src_ph2') == {'referral': None, 'src': 'ph2'}
    assert User.analyze_initial_data('/start src_ph_2') == {'referral': None}
    assert User.analyze_initial_data('/start referral_123') == {'referral': '123'}
    assert User.analyze_initial_data('/start chat_123') == {'referral': None, 'chat': '123'}
    assert User.analyze_initial_data('/start j_123') == {'referral': None, 'j': '123'}
    assert User.analyze_initial_data('/start src_untrusted') == {'referral': None}


async def test_ph_first_touch_existing_user_and_start_redelivery(bench: Bench):
    """new PH source is immutable; an existing account gets a touch, and redelivery is idempotent"""
    from pkg.service.user import User

    new_user = await User.register(OWNER['id'], 'ru', {'referral': None, 'src': 'ph2'}, 'start:99101:1')
    assert new_user['user']['first_source'] == 'ph2'
    await User.register(OWNER['id'], 'ru', {'referral': None, 'src': 'ph2'}, 'start:99101:1')
    await User.register(OWNER['id'], 'ru', {'referral': None, 'src': 'ph2'}, 'start:99101:2')

    events = await bench.sql("SELECT event_key, is_new_user FROM attribution_events WHERE event_type = 'bot_start'")
    assert len(events) == 2, events
    assert events[0]['is_new_user'] is True
    assert events[1]['is_new_user'] is False
    [user] = await bench.sql('SELECT first_source FROM users WHERE service_id = $1', str(OWNER['id']))
    assert user['first_source'] == 'ph2'


async def test_private_start_command_records_one_ph_touch_on_redelivery(bench: Bench):
    """the real private /start route attributes the campaign once when Telegram redelivers its message"""
    message = bench._message({'id': OWNER['id'], 'type': 'private', 'first_name': 'PH'}, OWNER, '/start src_ph2')
    await bench.feed({'message': message})
    await bench.feed({'message': message})
    [user] = await bench.sql('SELECT first_source FROM users WHERE service_id = $1', str(OWNER['id']))
    assert user['first_source'] == 'ph2'
    assert len(await bench.sql("SELECT id FROM attribution_events WHERE event_type = 'bot_start'")) == 1


async def test_old_user_source_stays_unknown_on_ph_start(bench: Bench):
    """an existing direct/legacy account is not relabelled as a new PH registration"""
    from pkg.service.user import User

    old_user = await bench.owner(OWNER)
    await bench.sql('UPDATE users SET first_source = NULL WHERE id = $1', old_user['id'])
    await User.register(OWNER['id'], 'ru', {'referral': None, 'src': 'ph2'}, 'start:99101:3')
    [row] = await bench.sql('SELECT first_source FROM users WHERE id = $1', old_user['id'])
    assert row['first_source'] is None
    [event] = await bench.sql("SELECT is_new_user FROM attribution_events WHERE event_type = 'bot_start'")
    assert event['is_new_user'] is False


async def test_group_connection_and_reconnection_are_distinct_successes(bench: Bench):
    """only new successful links create records; reconnect after removal gets a new connection event"""
    from pkg.service.chat import Chat
    from pkg.service.user import User

    owner = (await User.register(OWNER['id'], 'ru', {'referral': None, 'src': 'ph2'}))['user']
    bench.group_in_telegram(GROUP, owner)
    first = await Chat.add(GROUP, OWNER['id'])
    assert 'error' not in first
    duplicate = await Chat.add(GROUP, OWNER['id'])
    assert duplicate['error'] == 'connection_exists'
    assert len(await bench.sql("SELECT id FROM attribution_events WHERE event_type = 'group_connected'")) == 1

    await Chat.delete(first['moderated_chat_id'], OWNER['id'])
    second = await Chat.add(GROUP, OWNER['id'])
    assert 'error' not in second
    events = await bench.sql("SELECT event_key, owner FROM attribution_events WHERE event_type = 'group_connected'")
    assert len(events) == 2, events
    assert all(row['owner'] is True for row in events)
    assert owner['first_source'] == 'ph2'


async def test_tariff_charge_trial_bonus_funding_and_duplicate_callback(bench: Bench):
    """only a real debit for a paid tariff is sales; duplicate operation key does not debit twice"""
    from pkg.service.tariff import Tariff
    from pkg.service.user import User

    owner = (await User.register(OWNER['id'], 'ru', {'referral': None, 'src': 'ph2'}))['user']
    await Tariff.add_amount(owner['id'], 90000, 'rub')
    await Tariff.activate_trial(await Tariff.user_tariff_info(owner['id']))
    assert not await bench.sql("SELECT id FROM attribution_events WHERE event_type = 'owner_subscription_charged'")
    # Expire the trial, return to free, then buy. The callback id is the idempotency key.
    await Tariff.change(owner['id'], 0, force=True)
    await Tariff.change(owner['id'], 1, charge_event_key='tariff-callback:test-1')
    balance_after_charge = (await bench.sql(
        "SELECT balance FROM user_balances WHERE user_id = $1 AND currency_code = 'rub'", owner['id']))[0]['balance']
    assert balance_after_charge == 60000
    rows = await bench.sql("SELECT amount_minor, currency_code FROM attribution_events "
                           "WHERE event_type = 'owner_subscription_charged'")
    assert rows == [{'amount_minor': 30000, 'currency_code': 'rub'}]

    # A bonus/forced switch changes entitlement without recording a sale.
    await Tariff.change(owner['id'], 0, force=True)
    await Tariff.change(owner['id'], 1, force=True)
    assert len(await bench.sql("SELECT id FROM attribution_events WHERE event_type = 'owner_subscription_charged'")) == 1


async def test_autorenew_is_charged_and_trial_is_not(bench: Bench):
    """the hourly renewal records its actual debit; an activated trial does not"""
    from pkg.repository import tariff_repository
    from pkg.service.tariff import Tariff
    from pkg.service.user import User

    owner = (await User.register(OWNER['id'], 'ru', {'referral': None, 'src': 'ph2'}))['user']
    await Tariff.add_amount(owner['id'], 30000, 'rub')
    await Tariff.change(owner['id'], 1, force=True)
    await Tariff.activate_trial(await Tariff.user_tariff_info(owner['id']))
    await bench.sql("UPDATE user_tariff_connections SET end_date = LOCALTIMESTAMP - interval '1 hour' "
                    "WHERE user_id = $1", owner['id'])
    processed = [row async for row in tariff_repository.process_subscriptions()]
    assert len(processed) == 1 and processed[0]['action'] == 'prolonged', processed
    [event] = await bench.sql("SELECT amount_minor, currency_code, details FROM attribution_events "
                              "WHERE event_type = 'owner_subscription_charged'")
    assert (event['amount_minor'], event['currency_code']) == (30000, 'rub')
    details = json.loads(event['details']) if isinstance(event['details'], str) else event['details']
    assert details['kind'] == 'renewal'


async def test_report_keeps_subscription_currencies_separate(bench: Bench):
    """the PH funnel groups money by currency instead of summing unlike units"""
    from pkg.repository import stats_repository
    from pkg.service.tariff import Tariff
    from pkg.service.user import User

    rub_owner = (await User.register(OWNER['id'], 'ru', {'referral': None, 'src': 'ph2'}))['user']
    usd_person = person(99104, 'ph-usd', 'en')
    usd_owner = (await User.register(usd_person['id'], 'en', {'referral': None, 'src': 'ph2'}))['user']
    await bench.sql("UPDATE users SET created_at = CURRENT_TIMESTAMP - interval '45 days' WHERE id = ANY($1)",
                    [rub_owner['id'], usd_owner['id']])
    await Tariff.add_amount(rub_owner['id'], 30000, 'rub')
    await Tariff.change(rub_owner['id'], 1, charge_event_key='tariff-rub')
    await Tariff.add_amount(usd_owner['id'], 450, 'usd')
    await Tariff.change(usd_owner['id'], 1, charge_event_key='tariff-usd')
    await bench.sql("UPDATE attribution_events e SET occurred_at = u.created_at + interval '15 days' "
                    "FROM users u WHERE u.id = e.user_id AND e.event_type = 'owner_subscription_charged'")

    report = await stats_repository.product_hunt_attribution()
    assert {row['currency_code'] for row in report['paid_by_currency']} == {'rub', 'usd'}, report


async def test_funding_duplicate_and_refund_are_separate_from_subscription(bench: Bench):
    """a duplicate funding callback credits once; balance refunds stay separate from tariff charges"""
    from pkg.service.payment import BalanceHandler
    from pkg.service.tariff import Tariff

    owner = await bench.owner(OWNER)
    payment = {'service': 'robokassa', 'user_id': owner['id'], 'amount': 75000, 'currency': 'rub', 'id': 'ph-fund'}
    await BalanceHandler.funding(payment)
    await BalanceHandler.funding(payment)
    assert not await bench.sql("SELECT id FROM attribution_events WHERE event_type = 'owner_subscription_charged'")

    refund = {'user_id': owner['id'], 'payment_service': 'test_refund', 'amount': -12000,
              'currency_code': 'rub', 'external_payment_id': 'ph-refund'}
    await Tariff.add_amount_with_payment_history(owner['id'], -12000, 'rub', refund)
    await Tariff.add_amount_with_payment_history(owner['id'], -12000, 'rub', refund)
    rows = await bench.sql("SELECT amount_minor, currency_code FROM attribution_events "
                           "WHERE event_type = 'owner_balance_refunded'")
    assert rows == [{'amount_minor': 12000, 'currency_code': 'rub'}]


async def test_admin_stats_include_ph_report_only_for_admin(bench: Bench):
    """the funnel appears in the existing stats command only for bot administrators"""
    owner = person(99102, 'admin', 'ru')
    await bench.owner(owner)
    await bench.sql('UPDATE users SET is_admin = TRUE WHERE service_id = $1', str(owner['id']))
    await bench.private_message(owner, '/stats')
    assert any('Product Hunt' in text for text in bench.telegram.texts_to(owner['id']))

    regular = person(99103, 'regular', 'ru')
    await bench.owner(regular)
    await bench.private_message(regular, '/stats')
    assert not any('Product Hunt' in text for text in bench.telegram.texts_to(regular['id']))


async def test_event_retention_removes_only_details_past_twelve_months(bench: Bench):
    """the hourly cleanup purges old detail but keeps recent attribution"""
    from pkg.repository import stats_repository
    from pkg.service.user import User

    owner = (await User.register(OWNER['id'], 'ru', {'referral': None, 'src': 'ph2'}, 'start:99101:4'))['user']
    await bench.sql("UPDATE attribution_events SET occurred_at = CURRENT_TIMESTAMP - interval '13 months'")
    await bench.sql("INSERT INTO attribution_events (event_key, event_type, user_id, touch_source) "
                    "VALUES ('recent-start', 'bot_start', $1, 'ph2')", owner['id'])
    assert await stats_repository.delete_expired_attribution_events() == 1
    [event] = await bench.sql('SELECT event_key FROM attribution_events')
    assert event['event_key'] == 'recent-start'
