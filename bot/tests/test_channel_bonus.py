"""+15 days for subscribing to the bot owner's channels: /admin adds them, the menu offers the bonus, the hourly
round pauses the free group of those who unsubscribe, subscribing again brings it back."""
import datetime
import json

from tests.bench import BOT_ID, BOT_USER, Bench, administrator, member, person

ADMIN = person(901, 'boss', 'ru')
OWNER = person(501, 'owner', 'ru')
CHANNEL = -1002000000001
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
    assert any('бесплатная группа теперь на паузе' in t for t in _texts(bench, OWNER)), _texts(bench, OWNER)
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
