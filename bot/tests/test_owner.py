"""The owner's side in private chat, through the real dispatcher: /start, the menu, the free trial."""
import json

from lib.language import localization
from tests.bench import Bench, person

OWNER_RU = person(501, 'owner', 'ru')
OWNER_EN = person(502, 'john', 'en')


async def test_start_registers_and_greets(bench: Bench):
    """/start registers the user on the free tariff and greets them in their language with a button to begin"""
    for user, lang in ((OWNER_RU, 'ru'), (OWNER_EN, 'en')):
        await bench.private_message(user, '/start')
        texts = bench.telegram.texts_to(user['id'])
        assert localization.get_message(['welcome', 'introduction'], lang) in texts, texts

        [greeting] = [call for call in bench.telegram.sent_to(user['id']) if call.reply_markup is not None
                      and getattr(call.reply_markup, 'inline_keyboard', None)]
        button = greeting.reply_markup.inline_keyboard[0][0]
        assert json.loads(button.callback_data) == {'tp': 'menu'}

    rows = await bench.sql('SELECT u.service_id, utc.tariff_id FROM users AS u '
                           'JOIN user_tariff_connections AS utc ON utc.user_id = u.id ORDER BY u.id')
    assert [(row['service_id'], row['tariff_id']) for row in rows] == [('501', 0), ('502', 0)]


async def test_start_twice_keeps_one_user(bench: Bench):
    """/start again does not make a second user or reset the tariff"""
    await bench.private_message(OWNER_RU, '/start')
    await bench.sql('UPDATE user_tariff_connections SET tariff_id = 2')
    await bench.private_message(OWNER_RU, '/start')
    rows = await bench.sql('SELECT utc.tariff_id FROM users AS u JOIN user_tariff_connections AS utc ON utc.user_id = u.id')
    assert [row['tariff_id'] for row in rows] == [2]


async def test_menu_starts_trial_once(bench: Bench):
    """the first menu says the 15-day trial started and what stays after it; the next one does not. Someone
    with no group is told where to start, and a balance short of the renewal is not raised two weeks early"""
    trial = localization.get_message(['subscription', 'free_trial'], 'en', days=15, groups=3)
    assert trial.startswith('🎁 <b>15 days of everything, free</b>') and 'one group stays free' in trial, trial
    await bench.private_message(OWNER_EN, '/start')
    bench.telegram.calls.clear()

    await bench.tap(OWNER_EN, json.dumps({'tp': 'menu'}))
    first = bench.telegram.texts_to(OWNER_EN['id']) + [
        call.text for call in bench.telegram.calls_of('editMessageText')]
    assert trial in first, first
    [menu] = [text for text in first if 'Main menu' in text]
    assert 'Start with <b>🆕 Add a group</b>' in menu and 'Insufficient' not in menu, menu

    bench.telegram.calls.clear()
    await bench.tap(OWNER_EN, json.dumps({'tp': 'menu'}))
    second = bench.telegram.texts_to(OWNER_EN['id']) + [
        call.text for call in bench.telegram.calls_of('editMessageText')]
    assert trial not in second, second
    assert second, 'the menu is shown again'


async def test_start_by_referral_link(bench: Bench):
    """/start from a referral link registers the newcomer, remembers who invited them and tells the inviter"""
    await bench.private_message(OWNER_RU, '/start')
    bench.telegram.calls.clear()

    await bench.private_message(OWNER_EN, f"/start referral_{OWNER_RU['id']}")
    [newcomer] = await bench.sql('SELECT ref_id FROM users WHERE service_id = $1', str(OWNER_EN['id']))
    [inviter] = await bench.sql('SELECT id FROM users WHERE service_id = $1', str(OWNER_RU['id']))
    assert newcomer['ref_id'] == inviter['id']
    assert localization.get_message(['welcome', 'introduction'], 'en') in bench.telegram.texts_to(OWNER_EN['id'])
    assert bench.telegram.texts_to(OWNER_RU['id']) == [
        localization.get_message(['subscription', 'fund', 'from_referral', 'initialed'], 'ru')]
