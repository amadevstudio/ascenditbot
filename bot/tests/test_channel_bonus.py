"""+15 days for subscribing to the bot owner's channels: /admin adds them, the menu offers the bonus, the hourly
round pauses the free group of those who unsubscribe, subscribing again brings it back. A channel left takes
its share of the days off a running term, once, whether the bot hears of it at once or in the daily check."""
import datetime
import json

from tests.bench import BOT_ID, BOT_USER, Bench, administrator, member, person

ADMIN = person(901, 'boss', 'ru')
OWNER = person(501, 'owner', 'ru')
CHANNEL = -1002000000001
CHANNEL_2 = -1002000000002
GROUP = -1001000000001


def _texts(bench: Bench, user: dict) -> list[str]:
    return [getattr(c, 'text', None) or '' for c in bench.telegram.calls_of('sendMessage', 'editMessageText')
            if int(c.chat_id or 0) == user['id']]


def _buttons(call) -> list[dict]:
    rows = getattr(call.reply_markup, 'inline_keyboard', None) or []
    return [{'text': b.text, 'data': json.loads(b.callback_data) if b.callback_data else None, 'url': b.url}
            for row in rows for b in row]


def _last(bench: Bench, user: dict):
    return [c for c in bench.telegram.calls_of('sendMessage', 'editMessageText') if int(c.chat_id or 0) == user['id']][-1]


async def _channel(bench: Bench):
    """The bot's admin adds the channel with /addchannel; the bot is an admin there."""
    await bench.owner(ADMIN)
    await bench.sql('UPDATE users SET is_admin = true WHERE service_id = $1', str(ADMIN['id']))
    bench.telegram.answers['getChat'] = lambda method: {
        'id': CHANNEL, 'type': 'channel', 'title': 'Ascendit News', 'username': 'ascendit_news',
        'accent_color_id': 0, 'max_reaction_count': 11, 'accepted_gift_types': {
            'unlimited_gifts': False, 'limited_gifts': False, 'unique_gifts': False,
            'premium_subscription': False, 'gifts_from_channels': False}} \
        if str(method.chat_id) in ('@ascendit_news', str(CHANNEL)) else bench.telegram._answer(bench.bot, method)
    bench.telegram.members[(CHANNEL, BOT_ID)] = administrator(BOT_USER)
    bench.telegram.members[(CHANNEL, ADMIN['id'])] = member(ADMIN)
    await bench.private_message(ADMIN, '/addchannel https://t.me/ascendit_news')
    del bench.telegram.answers['getChat']


async def test_admin_adds_and_removes_channels(bench: Bench):
    """/admin lists the channels, /addchannel adds one the bot can check, 🗑 removes it; others get no page"""
    await _channel(bench)
    page = _last(bench, ADMIN)
    assert 'Ascendit News' in page.text and 'взяли бонус 0' in page.text, page.text
    [row] = await bench.sql('SELECT service_id, link FROM promo_channels')
    assert row == {'service_id': str(CHANNEL), 'link': 'https://t.me/ascendit_news'}

    await bench.owner(OWNER)
    bench.telegram.calls.clear()
    await bench.private_message(OWNER, '/admin')
    assert not any('Каналы за подписку' in t for t in _texts(bench, OWNER))

    [remove] = _buttons(page)
    await bench.tap(ADMIN, json.dumps(remove['data']))
    assert await bench.sql('SELECT * FROM promo_channels') == []


async def test_renamed_channel_shows_its_new_link(bench: Bench):
    """the channel's @username changed: opening the bonus page shows and stores the new title and link, no
    new /addchannel; Telegram not answering keeps the stored ones"""
    await _channel(bench)
    await bench.owner(OWNER)
    await bench.tap(OWNER, json.dumps({'tp': 'bonus'}))
    assert 'https://t.me/ascendit_news' in [b['url'] for b in _buttons(_last(bench, OWNER))]

    bench.telegram.answers['getChat'] = lambda method: {
        'id': CHANNEL, 'type': 'channel', 'title': 'Ascendit Channel', 'username': 'ascendit_channel',
        'accent_color_id': 0, 'max_reaction_count': 11, 'accepted_gift_types': {
            'unlimited_gifts': False, 'limited_gifts': False, 'unique_gifts': False,
            'premium_subscription': False, 'gifts_from_channels': False}}
    await bench.tap(OWNER, json.dumps({'tp': 'bonus'}))
    page = _last(bench, OWNER)
    assert 'Ascendit Channel' in page.text and 'https://t.me/ascendit_channel' in [b['url'] for b in _buttons(page)]
    [row] = await bench.sql('SELECT title, link FROM promo_channels')
    assert row == {'title': 'Ascendit Channel', 'link': 'https://t.me/ascendit_channel'}, row

    del bench.telegram.answers['getChat']
    await bench.tap(OWNER, json.dumps({'tp': 'bonus'}))
    assert 'https://t.me/ascendit_channel' in [b['url'] for b in _buttons(_last(bench, OWNER))]


async def test_subscribe_for_days_then_unsubscribe_pauses_the_free_group(bench: Bench):
    """the menu offers the bonus; not subscribed, no days; subscribed, 15 days on top of the trial. On the free
    tariff, unsubscribing pauses the free group and says so; subscribing again brings it back"""
    await _channel(bench)
    owner = await bench.owner(OWNER)
    await bench.private_message(OWNER, '/start')
    await bench.tap(OWNER, json.dumps({'tp': 'menu'}))
    [trial_end] = [r['end_date'] for r in await bench.sql('SELECT end_date FROM user_tariff_connections WHERE user_id = $1', owner['id'])]
    assert trial_end is not None, 'the menu started the trial'
    assert '🎁 +15 дней за подписку' in [b['text'] for b in _buttons(_last(bench, OWNER))]
    await bench.tap(OWNER, json.dumps({'tp': 'bonus'}))
    offer = _last(bench, OWNER)
    assert 'Ascendit News' in offer.text and 'Условие: если потом отпишетесь' in offer.text, offer.text
    assert 'https://t.me/ascendit_news' in [b['url'] for b in _buttons(offer)]

    await bench.tap(OWNER, json.dumps({'tp': 'bonus_check'}))
    [alert] = bench.telegram.calls_of('answerCallbackQuery')[-1:]
    assert alert.show_alert and 'Ascendit News' in alert.text, alert
    assert await bench.sql('SELECT * FROM channel_bonus_claims') == []

    bench.telegram.members[(CHANNEL, OWNER['id'])] = member(OWNER)
    await bench.tap(OWNER, json.dumps({'tp': 'bonus_check'}))
    assert 'Готово: +15 дней' in _last(bench, OWNER).text, _last(bench, OWNER).text
    [end] = [r['end_date'] for r in await bench.sql('SELECT end_date FROM user_tariff_connections WHERE user_id = $1', owner['id'])]
    assert abs((end - trial_end) - datetime.timedelta(days=15)) < datetime.timedelta(minutes=1), (trial_end, end)
    await bench.tap(OWNER, json.dumps({'tp': 'bonus_check'}))
    [end_again] = [r['end_date'] for r in await bench.sql('SELECT end_date FROM user_tariff_connections WHERE user_id = $1', owner['id'])]
    assert end_again == end, 'the bonus is given once'

    # The term is over: the free tariff with one group; then they leave the channel
    chat = await bench.group(GROUP, owner)
    await bench.sql('UPDATE user_tariff_connections SET tariff_id = 0, end_date = NULL')
    await bench.sql("UPDATE channel_bonus_claims SET checked_at = LOCALTIMESTAMP - interval '2 days'")
    bench.telegram.members[(CHANNEL, OWNER['id'])] = {'status': 'left', 'user': OWNER}
    bench.telegram.calls.clear()
    from pkg.background.async_tasks.subscription_handler import subscription_handler_round
    await subscription_handler_round()
    assert (await bench.sql('SELECT disabled FROM moderated_chats WHERE id = $1', chat['id']))[0]['disabled'] is True
    assert any('Бесплатная группа теперь на паузе' in t for t in _texts(bench, OWNER)), _texts(bench, OWNER)
    await bench.tap(OWNER, json.dumps({'tp': 'menu'}))
    assert 'бесплатная группа на паузе' in _last(bench, OWNER).text
    assert '🔔 Вернуть бесплатную группу' in [b['text'] for b in _buttons(_last(bench, OWNER))]

    bench.telegram.members[(CHANNEL, OWNER['id'])] = member(OWNER)
    await bench.tap(OWNER, json.dumps({'tp': 'bonus'}))
    await bench.tap(OWNER, json.dumps({'tp': 'bonus_check'}))
    assert 'Бесплатная группа снова работает' in _last(bench, OWNER).text, _last(bench, OWNER).text
    assert (await bench.sql('SELECT disabled FROM moderated_chats WHERE id = $1', chat['id']))[0]['disabled'] is False


async def test_bonus_not_offered_without_channels(bench: Bench):
    """no channels listed: the menu has no bonus button"""
    await bench.owner(OWNER)
    await bench.private_message(OWNER, '/start')
    await bench.tap(OWNER, json.dumps({'tp': 'menu'}))
    assert not any('за подписку' in b['text'] for b in _buttons(_last(bench, OWNER)))


async def _end_date(bench: Bench, owner: dict) -> datetime.datetime:
    [row] = await bench.sql('SELECT end_date FROM user_tariff_connections WHERE user_id = $1', owner['id'])
    return row['end_date']


async def _took_bonus_for_two_channels(bench: Bench) -> dict:
    """The owner on the trial took the bonus for two channels; 15 / 2 rounded up is 8 days a channel."""
    await _channel(bench)
    await bench.sql("INSERT INTO promo_channels (service_id, title, link) VALUES ($1, 'Second', 'https://t.me/second')",
                    str(CHANNEL_2))
    owner = await bench.owner(OWNER)
    await bench.private_message(OWNER, '/start')
    await bench.tap(OWNER, json.dumps({'tp': 'menu'}))
    for channel in (CHANNEL, CHANNEL_2):
        bench.telegram.members[(channel, OWNER['id'])] = member(OWNER)
    await bench.tap(OWNER, json.dumps({'tp': 'bonus'}))
    assert 'за каждый канал из срока снимется дней: 8' in _last(bench, OWNER).text, _last(bench, OWNER).text
    await bench.tap(OWNER, json.dumps({'tp': 'bonus_check'}))
    assert 'Готово: +15 дней' in _last(bench, OWNER).text, _last(bench, OWNER).text
    return owner


async def _membership(bench: Bench, channel: int, old: dict, new: dict):
    """What Telegram sends the channel's admins when someone joins or leaves"""
    bench.telegram.members[(channel, OWNER['id'])] = new
    await bench.feed({'chat_member': {
        'chat': {'id': channel, 'type': 'channel', 'title': 'Channel'}, 'from': OWNER,
        'date': int(datetime.datetime.now().timestamp()), 'old_chat_member': old, 'new_chat_member': new}})


def _days(delta: datetime.timedelta) -> float:
    return round(delta / datetime.timedelta(days=1), 3)


async def test_leaving_a_channel_takes_its_days_once(bench: Bench):
    """left a channel: 8 days off at once and told so; back and gone again: nothing more; the second channel,
    seen in the daily check: the remaining 7, so leaving both takes the 15 and no more"""
    # Polling asks Telegram for the update types the routers handle: without this the leave never comes
    assert 'chat_member' in bench.dispatcher.resolve_used_update_types()
    owner = await _took_bonus_for_two_channels(bench)
    with_bonus = await _end_date(bench, owner)
    left = {'status': 'left', 'user': OWNER}

    bench.telegram.calls.clear()
    await _membership(bench, CHANNEL, member(OWNER), left)
    assert _days(with_bonus - await _end_date(bench, owner)) == 8
    [notice] = _texts(bench, OWNER)
    assert 'Из срока снято дней: 8' in notice and 'Когда тариф закончится' in notice, notice

    await _membership(bench, CHANNEL, left, member(OWNER))
    bench.telegram.calls.clear()
    await _membership(bench, CHANNEL, member(OWNER), left)
    assert _days(with_bonus - await _end_date(bench, owner)) == 8, 'a channel takes its days once'
    assert not any('снято' in t for t in _texts(bench, OWNER)), _texts(bench, OWNER)

    bench.telegram.members[(CHANNEL_2, OWNER['id'])] = left
    await bench.sql("UPDATE channel_bonus_claims SET checked_at = LOCALTIMESTAMP - interval '2 days'")
    bench.telegram.calls.clear()
    from pkg.background.async_tasks.subscription_handler import subscription_handler_round
    await subscription_handler_round()
    assert _days(with_bonus - await _end_date(bench, owner)) == 15
    assert any('Из срока снято дней: 7' in t for t in _texts(bench, OWNER)), _texts(bench, OWNER)


async def test_days_taken_never_go_below_now(bench: Bench):
    """2 days left and a channel left: the term ends now, not 6 days ago"""
    owner = await _took_bonus_for_two_channels(bench)
    await bench.sql("UPDATE user_tariff_connections SET end_date = LOCALTIMESTAMP + interval '2 days'")
    await _membership(bench, CHANNEL, member(OWNER), {'status': 'left', 'user': OWNER})
    [now] = await bench.sql('SELECT LOCALTIMESTAMP AS now')
    assert abs(_days(await _end_date(bench, owner) - now['now'])) < 0.01


async def test_free_tariff_leave_takes_no_days_and_keeps_the_channel_share(bench: Bench):
    """on the free tariff a leave only pauses the free group: no term to take from, so the channel's days are
    still there to take once a term runs"""
    owner = await _took_bonus_for_two_channels(bench)
    await bench.sql('UPDATE user_tariff_connections SET tariff_id = 0, end_date = NULL')
    left = {'status': 'left', 'user': OWNER}
    await _membership(bench, CHANNEL, member(OWNER), left)
    [claim] = await bench.sql('SELECT penalized_channel_ids, lost_at FROM channel_bonus_claims')
    assert claim['penalized_channel_ids'] == [] and claim['lost_at'] is not None, claim

    # A term runs again (paid), still not subscribed: the daily check takes the channel's 8 days now
    await bench.sql("UPDATE user_tariff_connections SET tariff_id = 1, end_date = LOCALTIMESTAMP + interval '20 days'")
    paid_until = await _end_date(bench, owner)
    await bench.sql("UPDATE channel_bonus_claims SET checked_at = LOCALTIMESTAMP - interval '2 days'")
    from pkg.background.async_tasks.subscription_handler import subscription_handler_round
    await subscription_handler_round()
    assert _days(paid_until - await _end_date(bench, owner)) == 8
