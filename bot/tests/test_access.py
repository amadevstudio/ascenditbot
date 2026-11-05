"""The way into a group through the bot: the owner's settings (by request, paid with prices and a way to pay),
the member's page (ask, pick a term, "I paid"), the managers' answers, extending, falling back to requests, the
member's reminders."""
import datetime
import json

from tests.bench import Bench, person

GROUP = -1001000000001
OWNER = person(501, 'owner', 'ru')
HELPER = person(502, 'helper', 'ru')
BUYER = person(701, 'buyer', 'ru')
OTHER = person(702, 'other', 'en')


def _buttons(call) -> list[dict]:
    rows = getattr(call.reply_markup, 'inline_keyboard', None) or []
    return [{'text': b.text, 'data': json.loads(b.callback_data) if b.callback_data else None, 'url': b.url}
            for row in rows for b in row]


def _last_to(bench: Bench, user: dict):
    calls = [call for call in bench.telegram.calls_of('sendMessage', 'editMessageText')
             if int(call.chat_id or 0) == user['id']]
    assert calls, f'nothing to {user["id"]}'
    return calls[-1]


def _press(call, text: str) -> str:
    button = next((b for b in _buttons(call) if text in b['text']), None)
    assert button is not None, f'no {text!r} in {[b["text"] for b in _buttons(call)]}'
    return json.dumps(button['data'], separators=(',', ':'))


async def _scene(bench: Bench, paid: bool = True, **access) -> dict:
    owner = await bench.owner(OWNER)
    if paid:
        await bench.sql("UPDATE user_tariff_connections SET tariff_id = 1, "
                        "end_date = LOCALTIMESTAMP + interval '30 days'")
    chat = await bench.group(GROUP, owner)
    if access:
        sets = ', '.join(f'{name} = ${i + 2}' for i, name in enumerate(access))
        await bench.sql(f'UPDATE moderated_chats SET {sets} WHERE id = $1', chat['id'], *access.values())
    return chat


PLANS = json.dumps([{'days': 7, 'amount': '300', 'currency': 'RUB'}, {'days': 30, 'amount': '1000', 'currency': 'RUB'}])


async def _paid_scene(bench: Bench) -> dict:
    return await _scene(bench, access_mode='paid', access_plans=PLANS, access_payment='https://pay.example/owner',
                        access_terms='Только авто. Связь: @owner')


# Prices

async def test_prices_are_read_the_way_people_write_them(bench: Bench):
    """prices: days, weeks, months, forever, symbols before or after, "1 000", one currency, sorted, bad lines"""
    from pkg.service.access import days_text, parse_plans, plan_text

    plans, bad = parse_plans("30 дней 1 000 ₽\n7 300\nнавсегда – 3000\nмесяц 1000\nнеделя: 300р\nерунда", 'RUB')
    assert bad == ['ерунда'], bad
    assert [(p['days'], p['amount'], p['currency']) for p in plans] == [
        (7, '300', 'RUB'), (30, '1000', 'RUB'), (0, '3000', 'RUB')], plans

    plans, bad = parse_plans("$10 month\n1 week 3.5$\n2 weeks 6 usd", 'RUB')
    assert not bad and [(p['days'], p['amount'], p['currency']) for p in plans] == [
        (7, '3.5', 'USD'), (14, '6', 'USD'), (30, '10', 'USD')], (plans, bad)
    assert plan_text(plans[0], 'en') == '7 days – $3.5'
    assert plan_text({'days': 0, 'amount': '1500', 'currency': 'RUB'}, 'ru') == 'навсегда – 1 500 ₽'
    assert [days_text(n, 'ru') for n in (1, 2, 5, 11, 21, 22, 30)] == [
        '1 день', '2 дня', '5 дней', '11 дней', '21 день', '22 дня', '30 дней']
    assert parse_plans("30", 'RUB')[1] == ['30'] and parse_plans("0 100", 'RUB')[0][0]['days'] == 0


# The owner's side

async def test_owner_walks_through_paid_entry(bench: Bench):
    """paid entry: locked on the free tariff; on a paid one, prices (step 1) then the way to pay (step 2)"""
    chat = await _scene(bench, paid=False)
    await bench.private_message(OWNER, f'/start chat_{chat["id"]}')
    await bench.tap(OWNER, '{"tp":"chat_access"}')
    page = _last_to(bench, OWNER)
    assert '🔒 💳 За плату' in [b['text'] for b in _buttons(page)], _buttons(page)
    await bench.tap(OWNER, '{"tp":"acc_mode","m":"paid"}')
    assert 'платных тарифах' in bench.telegram.calls_of('answerCallbackQuery')[-1].text
    [row] = await bench.sql('SELECT access_mode FROM moderated_chats')
    assert row['access_mode'] == 'off'

    await bench.sql("UPDATE user_tariff_connections SET tariff_id = 1, end_date = LOCALTIMESTAMP + interval '30 days'")
    await bench.tap(OWNER, '{"tp":"acc_mode","m":"paid"}')
    assert 'Шаг 1 из 2' in _last_to(bench, OWNER).text
    await bench.private_message(OWNER, 'ерунда')
    assert 'Не понял строки' in _last_to(bench, OWNER).text
    await bench.private_message(OWNER, '7 300\n30 1000')
    assert 'Шаг 2 из 2' in _last_to(bench, OWNER).text
    await bench.private_message(OWNER, 'https://pay.example/owner')
    page = _last_to(bench, OWNER)
    assert '7 дней – 300 ₽ · 30 дней – 1 000 ₽' in page.text and 'https://pay.example/owner' in page.text, page.text
    assert f'start=j_{chat["id"]}' in page.text

    await bench.tap(OWNER, '{"tp":"acc_edit","f":"terms"}')
    await bench.private_message(OWNER, 'x' * 1001)
    assert 'Слишком длинно' in _last_to(bench, OWNER).text
    await bench.private_message(OWNER, 'Только авто')
    await bench.tap(OWNER, '{"tp":"acc_edit","f":"terms"}')
    await bench.private_message(OWNER, '-')
    [row] = await bench.sql('SELECT access_mode, access_terms, access_payment, access_plans FROM moderated_chats')
    assert row['access_mode'] == 'paid' and row['access_terms'] is None and row['access_payment'], row
    assert [plan['days'] for plan in json.loads(row['access_plans'])] == [7, 30]


async def test_owner_posts_the_button_in_the_group(bench: Bench):
    """"Button in the group": a message with a link to the group's page in the bot, pinned"""
    chat = await _scene(bench, access_mode='request')
    await bench.private_message(OWNER, f'/start chat_{chat["id"]}')
    await bench.tap(OWNER, '{"tp":"chat_access"}')
    await bench.tap(OWNER, '{"tp":"acc_post"}')
    # First what it is: the message the members will see; nothing posted yet
    confirm = _last_to(bench, OWNER)
    assert 'опубликует в группе такое сообщение' in confirm.text and 'Получить доступ' in confirm.text, confirm.text
    assert not [call for call in bench.telegram.calls_of('sendMessage') if int(call.chat_id) == GROUP]
    await bench.tap(OWNER, _press(confirm, 'Опубликовать и закрепить'))
    [post] = [call for call in bench.telegram.calls_of('sendMessage') if int(call.chat_id) == GROUP]
    assert _buttons(post)[0]['url'].endswith(f'start=j_{chat["id"]}')
    assert bench.telegram.calls_of('pinChatMessage')
    # Posting again replaces the old message
    await bench.tap(OWNER, '{"tp":"acc_post_go"}')
    assert len([call for call in bench.telegram.calls_of('deleteMessage') if int(call.chat_id) == GROUP]) == 1
    assert len([call for call in bench.telegram.calls_of('sendMessage') if int(call.chat_id) == GROUP]) == 2


# The member's side, paid

async def test_member_pays_by_the_owners_link_and_the_owner_confirms(bench: Bench):
    """deleted message → the link; the page; a term; "I paid" → the managers; confirm → 30 days, the member told"""
    chat = await _paid_scene(bench)
    await bench.group_message(GROUP, BUYER, 'Продам гараж')
    [notice] = [call for call in bench.telegram.calls_of('sendMessage') if int(call.chat_id) == GROUP]
    assert f'start=j_{chat["id"]}' in notice.text and notice.ephemeral_message_parameters
    # No alert about a stranger: the owner gets requests instead
    assert not [call for call in bench.telegram.calls_of('sendMessage') if int(call.chat_id) == OWNER['id']]

    await bench.private_message(BUYER, f'/start j_{chat["id"]}')
    page = _last_to(bench, BUYER)
    assert 'Только авто' in page.text and '30 дней – 1 000 ₽' in [b['text'] for b in _buttons(page)], page.text
    await bench.tap(BUYER, _press(page, '30 дней'))
    plan = _last_to(bench, BUYER)
    assert [b['url'] for b in _buttons(plan) if b['url']] == ['https://pay.example/owner']
    await bench.tap(BUYER, _press(plan, 'Я оплатил'))
    await bench.tap(BUYER, _press(plan, 'Я оплатил'))  # twice: one request

    [request] = await bench.sql('SELECT kind, days, amount, status FROM access_requests')
    assert request['kind'] == 'paid_manual' and request['days'] == 30 and request['status'] == 'pending'
    alert = _last_to(bench, OWNER)
    assert 'сообщает об оплате: 30 дней – 1 000 ₽' in alert.text, alert.text
    assert 'Об оплате сообщили' in _last_to(bench, BUYER).text

    await bench.tap(OWNER, _press(alert, 'Подтвердить: 30 дней'))
    [entry] = await bench.sql('SELECT nickname, user_service_id, expires_at FROM allowed_users')
    assert entry['user_service_id'] == str(BUYER['id'])
    assert datetime.timedelta(days=29) < entry['expires_at'] - datetime.datetime.now() <= datetime.timedelta(days=30)
    assert 'открыт до' in _last_to(bench, OWNER).text
    told = _last_to(bench, BUYER)
    assert 'Владелец открыл вам доступ' in told.text, told.text

    # Writes now; the request is closed, a second tap says so
    bench.telegram.calls.clear()
    await bench.group_message(GROUP, BUYER, 'Продам гараж')
    assert not bench.telegram.calls_of('deleteMessage')
    await bench.tap(OWNER, _press(alert, 'Подтвердить: 30 дней'))
    assert 'уже ответили' in _last_to(bench, OWNER).text

    # /access shows the group and its term, with a button to extend; the owner's /stats counts the payment
    await bench.private_message(BUYER, '/access')
    mine = _last_to(bench, BUYER)
    assert 'Где вы можете писать' in mine.text and ': до ' in mine.text, mine.text
    assert any('Продлить' in b['text'] and b['data'] == {'tp': 'jo', 'c': chat['id']} for b in _buttons(mine))
    await bench.private_message(OWNER, '/stats')
    assert 'Оплат за вход за 30 дней: 1, на 1 000 ₽' in _last_to(bench, OWNER).text


async def test_undo_after_a_payment_asks_about_the_payment(bench: Bench):
    """Undo under a confirmed payment asks: keep the access, take it away with the payment cancelled (not counted
    in /stats any more), or take it away and keep the payment"""
    chat = await _paid_scene(bench)
    await bench.private_message(BUYER, f'/start j_{chat["id"]}')
    await bench.tap(BUYER, _press(_last_to(bench, BUYER), '7 дней'))
    await bench.tap(BUYER, _press(_last_to(bench, BUYER), 'Я оплатил'))
    await bench.tap(OWNER, _press(_last_to(bench, OWNER), 'Подтвердить'))
    confirmed = _last_to(bench, OWNER)
    await bench.tap(OWNER, _press(confirmed, 'Отменить'))
    question = _last_to(bench, OWNER)
    assert 'Оплата была: 7 дней – 300 ₽' in question.text, question.text
    assert await bench.sql('SELECT 1 FROM allowed_users')  # nothing changed yet

    await bench.tap(OWNER, _press(question, 'Оставить доступ'))
    assert 'остаётся' in _last_to(bench, OWNER).text
    assert await bench.sql('SELECT 1 FROM allowed_users')

    await bench.tap(OWNER, _press(_last_to(bench, OWNER), 'Отменить'))
    await bench.tap(OWNER, _press(_last_to(bench, OWNER), 'оплату отменить'))
    assert 'Деньги верните сами' in _last_to(bench, OWNER).text
    assert not await bench.sql('SELECT 1 FROM allowed_users')
    [request] = await bench.sql('SELECT status FROM access_requests')
    assert request['status'] == 'revoked'
    await bench.private_message(OWNER, '/stats')
    assert 'Оплат за вход' not in _last_to(bench, OWNER).text


async def test_access_list_empty_and_waiting(bench: Bench):
    """/access with nothing says where the link comes from; a request waiting is listed with its group"""
    chat = await _scene(bench, access_mode='request')
    await bench.private_message(BUYER, '/access')
    assert 'Доступов через бота пока нет' in _last_to(bench, BUYER).text
    await bench.private_message(BUYER, f'/start j_{chat["id"]}')
    await bench.tap(BUYER, _press(_last_to(bench, BUYER), 'Попросить'))
    await bench.private_message(BUYER, '/access')
    mine = _last_to(bench, BUYER)
    assert 'ждёт ответа владельца' in mine.text, mine.text
    assert [b['data'] for b in _buttons(mine)] == [{'tp': 'jo', 'c': chat['id']}]


async def test_extending_adds_days_and_has_no_undo(bench: Bench):
    """paying again while the term runs adds the days to its end; the answer has no undo, which would wipe it"""
    chat = await _paid_scene(bench)
    await bench.sql("INSERT INTO allowed_users (moderated_chat_id, nickname, user_service_id, expires_at, "
                    "created_at, updated_at) VALUES ($1, 'buyer', '701', NOW() + interval '10 days', NOW(), NOW())",
                    chat['id'])
    await bench.private_message(BUYER, f'/start j_{chat["id"]}')
    page = _last_to(bench, BUYER)
    assert 'У вас есть доступ до' in page.text and 'дни добавятся' in page.text, page.text
    await bench.tap(BUYER, _press(page, '7 дней'))
    await bench.tap(BUYER, _press(_last_to(bench, BUYER), 'Я оплатил'))
    page = _last_to(bench, BUYER)
    assert 'Об оплате сообщили' in page.text, page.text
    assert [b['text'] for b in _buttons(page)] == ['✖️ Отменить заявку'], _buttons(page)

    await bench.tap(OWNER, _press(_last_to(bench, OWNER), 'Подтвердить'))
    [entry] = await bench.sql('SELECT expires_at FROM allowed_users')
    left = entry['expires_at'] - datetime.datetime.now()
    assert datetime.timedelta(days=16, hours=23) < left <= datetime.timedelta(days=17), left
    assert 'Отменить' not in [b['text'] for b in _buttons(_last_to(bench, OWNER))]


async def test_declined_payment(bench: Bench):
    """decline: the member is told to contact the owner; the page says it was declined, without buttons"""
    chat = await _paid_scene(bench)
    await bench.private_message(BUYER, f'/start j_{chat["id"]}')
    await bench.tap(BUYER, _press(_last_to(bench, BUYER), '7 дней'))
    await bench.tap(BUYER, _press(_last_to(bench, BUYER), 'Я оплатил'))
    await bench.tap(OWNER, _press(_last_to(bench, OWNER), 'Отклонить'))
    assert 'не подтвердил оплату' in _last_to(bench, BUYER).text
    assert not await bench.sql('SELECT 1 FROM allowed_users')
    await bench.private_message(BUYER, f'/start j_{chat["id"]}')
    page = _last_to(bench, BUYER)
    assert 'отклонил заявку' in page.text and not _buttons(page), page.text


async def test_decline_can_be_undone(bench: Bench):
    """a "no" by mistake: Undo puts the request back with its answers; confirming then lets the member in"""
    chat = await _paid_scene(bench)
    await bench.private_message(BUYER, f'/start j_{chat["id"]}')
    await bench.tap(BUYER, _press(_last_to(bench, BUYER), '7 дней'))
    await bench.tap(BUYER, _press(_last_to(bench, BUYER), 'Я оплатил'))
    alert = _last_to(bench, OWNER)
    await bench.tap(OWNER, _press(alert, 'Отклонить'))
    declined = _last_to(bench, OWNER)
    assert 'отклонена' in declined.text, declined.text

    # Later, from the menu: the group's "Outsiders" page lists the declined, each with Undo
    await bench.private_message(OWNER, f'/start chat_{chat["id"]}')
    await bench.tap(OWNER, '{"tp":"chat_access"}')
    page = _last_to(bench, OWNER)
    await bench.tap(OWNER, _press(page, 'Отклонённые (1)'))
    declined = _last_to(bench, OWNER)
    assert 'отклонена' in declined.text and '@buyer' in declined.text, declined.text
    bench.telegram.calls.clear()
    await bench.tap(OWNER, _press(declined, 'Отменить'))
    # Unmuted in the group at once
    [unmute] = bench.telegram.calls_of('restrictChatMember')
    assert int(unmute.user_id) == BUYER['id'] and unmute.permissions.can_send_messages
    again = _last_to(bench, OWNER)
    assert 'сообщает об оплате: 7 дней – 300 ₽' in again.text, again.text
    [request] = await bench.sql('SELECT status, decided_at FROM access_requests')
    assert request['status'] == 'pending' and request['decided_at'] is None
    await bench.private_message(BUYER, f'/start j_{chat["id"]}')
    assert 'Об оплате сообщили' in _last_to(bench, BUYER).text

    # A second Undo does nothing; confirming lets the member in
    await bench.tap(OWNER, _press(declined, 'Отменить'))
    assert 'уже ответили' in _last_to(bench, OWNER).text
    await bench.tap(OWNER, _press(again, 'Подтвердить: 7 дней'))
    assert await bench.sql('SELECT 1 FROM allowed_users')
    assert 'Владелец открыл вам доступ' in _last_to(bench, BUYER).text
    await bench.private_message(OWNER, f'/start chat_{chat["id"]}')
    await bench.tap(OWNER, '{"tp":"chat_access"}')
    assert not [b for b in _buttons(_last_to(bench, OWNER)) if 'Отклонённые' in b['text']]


async def test_member_cancels_the_request(bench: Bench):
    """"I paid" by mistake: the member cancels it and picks again; the owner's buttons say it is answered"""
    chat = await _paid_scene(bench)
    await bench.private_message(BUYER, f'/start j_{chat["id"]}')
    await bench.tap(BUYER, _press(_last_to(bench, BUYER), '7 дней'))
    await bench.tap(BUYER, _press(_last_to(bench, BUYER), 'Я оплатил'))
    alert = _last_to(bench, OWNER)
    await bench.tap(BUYER, _press(_last_to(bench, BUYER), 'Отменить заявку'))
    page = _last_to(bench, BUYER)
    assert 'Выберите срок' in page.text and '7 дней – 300 ₽' in [b['text'] for b in _buttons(page)], page.text
    [request] = await bench.sql('SELECT status FROM access_requests')
    assert request['status'] == 'cancelled'
    await bench.tap(OWNER, _press(alert, 'Подтвердить'))
    assert 'уже ответили' in _last_to(bench, OWNER).text
    assert not await bench.sql('SELECT 1 FROM allowed_users')


async def test_paid_entry_falls_back_to_requests_without_a_paid_tariff(bench: Bench):
    """the owner's tariff ended: members can still ask, for free"""
    chat = await _paid_scene(bench)
    await bench.sql('UPDATE user_tariff_connections SET tariff_id = 0')
    await bench.private_message(BUYER, f'/start j_{chat["id"]}')
    assert [b['text'] for b in _buttons(_last_to(bench, BUYER))] == ['📨 Попросить доступ']


# By request

async def test_request_on_the_free_tariff(bench: Bench):
    """by request: the member asks, terms locked on the free tariff, for good works; a stranger cannot answer"""
    chat = await _scene(bench, paid=False, access_mode='request')
    await bench.private_message(BUYER, f'/start j_{chat["id"]}')
    await bench.tap(BUYER, _press(_last_to(bench, BUYER), 'Попросить доступ'))
    alert = _last_to(bench, OWNER)
    assert 'Заявка на доступ' in alert.text and '🔒 ✅ 7 дней' in [b['text'] for b in _buttons(alert)]

    await bench.tap(OWNER, _press(alert, '7 дней'))
    assert 'платных тарифах' in bench.telegram.calls_of('answerCallbackQuery')[-1].text
    await bench.owner(OTHER)
    await bench.tap(OTHER, _press(alert, 'Навсегда'))
    assert not await bench.sql('SELECT 1 FROM allowed_users')

    await bench.tap(OWNER, _press(alert, 'Навсегда'))
    [entry] = await bench.sql('SELECT expires_at FROM allowed_users')
    assert entry['expires_at'] is None
    await bench.private_message(BUYER, f'/start j_{chat["id"]}')
    page = _last_to(bench, BUYER)
    assert 'У вас есть доступ к этой группе' in page.text and not _buttons(page)


async def test_off_and_unknown_groups(bench: Bench):
    """the way in off: the page says so and names nothing; an unknown group: not found"""
    chat = await _scene(bench)
    await bench.private_message(BUYER, f'/start j_{chat["id"]}')
    page = _last_to(bench, BUYER)
    assert 'не принимает заявки' in page.text and 'Group' not in page.text
    await bench.private_message(BUYER, '/start j_999')
    assert 'не найдена' in _last_to(bench, BUYER).text


async def test_every_manager_gets_the_request_and_one_answer_counts(bench: Bench):
    """two managers get the request; the second answer finds it answered"""
    chat = await _scene(bench, access_mode='request')
    helper = await bench.owner(HELPER)
    await bench.sql('INSERT INTO user_moderated_chat_connections (user_id, owner, moderated_chat_id, created_at, '
                    'updated_at) VALUES ($1, FALSE, $2, NOW(), NOW())', helper['id'], chat['id'])
    await bench.private_message(BUYER, f'/start j_{chat["id"]}')
    await bench.tap(BUYER, _press(_last_to(bench, BUYER), 'Попросить доступ'))
    owner_alert, helper_alert = _last_to(bench, OWNER), _last_to(bench, HELPER)
    await bench.tap(HELPER, _press(helper_alert, 'Отклонить'))
    await bench.tap(OWNER, _press(owner_alert, 'Навсегда'))
    assert 'уже ответили' in _last_to(bench, OWNER).text
    assert not await bench.sql('SELECT 1 FROM allowed_users')


# Reminders

async def test_member_hears_that_the_term_ends(bench: Bench):
    """a day before the end, and at the end, the member (who started the bot) gets a way to extend"""
    from pkg.service.member_alerts import MemberAlerts

    chat = await _paid_scene(bench)
    await bench.owner(BUYER)
    await bench.sql("INSERT INTO allowed_users (moderated_chat_id, nickname, user_service_id, expires_at, "
                    "created_at, updated_at) VALUES ($1, 'buyer', '701', NOW() + interval '20 hours', NOW(), NOW())",
                    chat['id'])
    await MemberAlerts.expiry_round()
    soon = _last_to(bench, BUYER)
    assert 'заканчивается' in soon.text and _buttons(soon)[0]['data'] == {'tp': 'jo', 'c': chat['id']}, soon.text

    await MemberAlerts.expiry_round(datetime.datetime.now() + datetime.timedelta(days=1))
    assert 'закончился' in _last_to(bench, BUYER).text


async def test_outsiders_quietly_or_tell_me_and_admins_on_the_join_page(bench: Bench):
    """"Outsiders": quietly turns the owner's alerts off, "tell me" back on, the group's page names the choice;
    the group's admin on the join page is told they need no access"""
    chat = await _scene(bench)
    await bench.private_message(OWNER, f'/start chat_{chat["id"]}')
    await bench.tap(OWNER, '{"tp":"chat_access"}')
    page = _last_to(bench, OWNER)
    assert 'Сообщение бот удаляет всегда' in page.text and 'Сейчас: 🔔 сообщать мне' in page.text, page.text
    assert '• 🔔 Сообщать мне' in [b['text'] for b in _buttons(page)]
    await bench.tap(OWNER, '{"tp":"acc_mode","m":"silent"}')
    [row] = await bench.sql('SELECT access_mode, owner_alerts FROM moderated_chats')
    assert row == {'access_mode': 'off', 'owner_alerts': False}
    assert 'Сейчас: 🔕 молча' in _last_to(bench, OWNER).text
    await bench.tap(OWNER, '{"tp":"acc_mode","m":"request"}')
    [row] = await bench.sql('SELECT access_mode FROM moderated_chats')
    assert row['access_mode'] == 'request'
    await bench.private_message(OWNER, f'/start chat_{chat["id"]}')
    assert '🚪 Посторонние: 📨 по заявке' in [b['text'] for b in _buttons(_last_to(bench, OWNER))]

    await bench.private_message(OWNER, f'/start j_{chat["id"]}')
    page = _last_to(bench, OWNER)
    assert 'Вы администратор' in page.text and 'Попросить' not in str(_buttons(page)), page.text
