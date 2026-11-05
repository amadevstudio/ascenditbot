"""The owner's tools: whitelist by id and for a term, "everyone writes", posting limits, alerts with one-tap
buttons, commands in the group, connecting a group by making the bot its admin, the group page, /stats."""
import ast
import datetime
import json
import os

from lib.language import localization
from tests.bench import BOT_ID, BOT_USER, Bench, administrator, member, person

GROUP = -1001000000001
OTHER_GROUP = -1001000000002
OWNER = person(501, 'owner', 'ru')
ADMIN = person(502, 'helper', 'en')
ALICE = person(601, 'Alice')
STRANGER = person(701, 'stranger', 'en')


async def _scene(bench: Bench, paid: bool = False, **chat_fields):
    owner = await bench.owner(OWNER)
    if paid:
        await bench.sql("UPDATE user_tariff_connections SET tariff_id = 1, "
                        "end_date = LOCALTIMESTAMP + interval '30 days'")
    chat = await bench.group(GROUP, owner, **chat_fields)
    return owner, chat


def _private_texts(bench: Bench, user: dict) -> list[str]:
    return bench.telegram.texts_to(user['id']) + [
        call.text for call in bench.telegram.calls_of('editMessageText') if int(call.chat_id or 0) == user['id']]


def _buttons(call) -> list[dict]:
    """The inline buttons of a sent message: text and parsed callback data (or url)."""
    rows = getattr(call.reply_markup, 'inline_keyboard', None) or []
    return [{'text': b.text, 'data': json.loads(b.callback_data) if b.callback_data else None, 'url': b.url}
            for row in rows for b in row]


def _deleted(bench: Bench) -> list[int]:
    return [call.message_id for call in bench.telegram.calls_of('deleteMessage')]


# Texts

def _literal_routes() -> list[tuple[str, list]]:
    """Every localization.get_message(['literal', 'route'], ...) in the bot's code."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    found = []
    for directory in ('pkg', 'framework', 'lib'):
        for path, _, files in os.walk(os.path.join(root, directory)):
            for file_name in files:
                if not file_name.endswith('.py'):
                    continue
                file_path = os.path.join(path, file_name)
                with open(file_path, encoding='utf-8') as file:
                    tree = ast.parse(file.read())
                for node in ast.walk(tree):
                    if not (isinstance(node, ast.Call) and getattr(node.func, 'attr', None) == 'get_message'
                            and getattr(node.func.value, 'id', None) == 'localization'
                            and node.args and isinstance(node.args[0], ast.List)):
                        continue
                    parts = node.args[0].elts
                    if all(isinstance(part, ast.Constant) for part in parts):
                        found.append((f'{file_path[len(root) + 1:]}:{node.lineno}', [p.value for p in parts]))
    return found


async def test_every_text_exists_in_both_languages(bench: Bench):
    """every text the code asks for by a fixed key exists in Russian and in English"""
    from project.i18n import routed_messages

    missing = []
    for where, route in _literal_routes():
        node = routed_messages
        for key in route:
            node = node.get(key.lower() if isinstance(key, str) else key) if isinstance(node, dict) else None
        if not isinstance(node, dict) or not node.get('ru') or not node.get('en'):
            missing.append(f'{where} {route}')
    assert not missing, '\n'.join(missing)


# Who may write

async def test_whitelisted_by_id_keeps_access_after_renaming(bench: Bench):
    """a member allowed by id writes under a new nickname: the message stays"""
    _, chat = await _scene(bench)
    from pkg.service.allowed_user import AllowedUser
    await AllowedUser.allow(chat['id'], user_service_id=str(ALICE['id']), nickname='old_name')
    await bench.group_message(GROUP, ALICE)
    assert not _deleted(bench), bench.telegram.calls


async def test_nickname_entry_learns_the_id(bench: Bench):
    """a member on the list by nickname writes: the bot remembers their id and name"""
    _, chat = await _scene(bench)
    await bench.whitelist(chat, 'Alice')
    await bench.group_message(GROUP, ALICE)
    [entry] = await bench.sql('SELECT user_service_id, display_name FROM allowed_users')
    assert entry == {'user_service_id': str(ALICE['id']), 'display_name': 'Test'}, entry


async def test_timed_access_ends(bench: Bench):
    """access that ended yesterday no longer lets the member write"""
    _, chat = await _scene(bench)
    await bench.whitelist(chat, 'Alice')
    await bench.sql("UPDATE allowed_users SET expires_at = LOCALTIMESTAMP - interval '1 day'")
    await bench.group_message(GROUP, ALICE)
    assert len(_deleted(bench)) == 1


async def test_everyone_can_write(bench: Bench):
    """in "everyone writes" mode a stranger's message stays"""
    await _scene(bench, everyone_can_write=True)
    await bench.group_message(GROUP, STRANGER)
    assert not _deleted(bench), bench.telegram.calls


async def test_telegram_forwards_stay(bench: Bench):
    """posts a linked channel forwards to the group (from 777000) stay"""
    await _scene(bench)
    await bench.group_message(GROUP, person(777000, None, first_name='Telegram'), is_automatic_forward=True)
    assert not _deleted(bench), bench.telegram.calls


# Posting limits

async def test_post_limit_on_paid_tariff(bench: Bench):
    """with 1 post a day, the second post of a member goes and they are told when they can post again"""
    await _scene(bench, paid=True, everyone_can_write=True, post_limit=1, post_limit_hours=24)
    await bench.group_message(GROUP, STRANGER, 'first ad')
    assert not _deleted(bench)
    second = await bench.group_message(GROUP, STRANGER, 'second ad')
    assert _deleted(bench) == [second['message_id']]
    [notice] = bench.telegram.sent_to(GROUP)
    assert notice.ephemeral_message_parameters.receiver_user_id == STRANGER['id']
    assert 'up to 1 a day' in notice.text, notice.text


async def test_post_limit_spares_admins(bench: Bench):
    """the owner posts as much as they like"""
    await _scene(bench, paid=True, post_limit=1, post_limit_hours=24)
    for _ in range(3):
        await bench.group_message(GROUP, OWNER)
    assert not _deleted(bench)


async def test_post_limit_window_slides(bench: Bench):
    """2 posts in 6 hours: the third waits for the first to be 6 hours old, not for a new calendar day"""
    from pkg.service.post_limit import PostLimit

    start = 1_800_000_000.0
    assert PostLimit.take(1, 2, 2, 6, now=start) is None
    assert PostLimit.take(1, 2, 2, 6, now=start + 3600) is None
    blocked = PostLimit.take(1, 2, 2, 6, now=start + 7200)
    assert blocked is not None and blocked.timestamp() == start + 6 * 3600
    assert PostLimit.take(1, 2, 2, 6, now=start + 6 * 3600 + 1) is None
    assert PostLimit.take(1, 3, 2, 6, now=start + 7200) is None, 'another member counts apart'


async def test_post_limit_words(bench: Bench):
    """the owner's own limit in words, Russian or English; nonsense is not a limit"""
    from pkg.service.post_limit import OFF, limit_text, parse_limit

    assert parse_limit('3 в час') == (3, 1)
    assert parse_limit('10 за 2 дня') == (10, 48)
    assert parse_limit('1 в неделю') == (1, 168)
    assert parse_limit('5 постов за 6 часов') == (5, 6)
    assert parse_limit('5/6h') == (5, 6)
    assert parse_limit('2 a day') == (2, 24)
    assert parse_limit('выкл') == OFF and parse_limit('off') == OFF and parse_limit('0') == OFF
    assert parse_limit('hello') is None and parse_limit('3') is None and parse_limit('1000 в день') is None
    assert parse_limit('1 за 2 месяца') is None
    assert limit_text(10, 48, 'ru') == '10 за 2 дня' and limit_text(5, 6, 'ru') == '5 за 6 часов'
    assert limit_text(3, 1, 'ru') == '3 в час' and limit_text(1, 168, 'en') == '1 a week'
    assert limit_text(2, 21, 'ru') == '2 за 21 час' and limit_text(None, None, 'ru') == 'без лимита'


async def test_post_limit_off_on_free_tariff(bench: Bench):
    """on the free tariff the limit is not applied"""
    await _scene(bench, everyone_can_write=True, post_limit=1, post_limit_hours=24)
    for _ in range(3):
        await bench.group_message(GROUP, STRANGER)
    assert not _deleted(bench)


# Alerts to the owner

async def _alert(bench: Bench) -> dict:
    [alert] = [call for call in bench.telegram.sent_to(OWNER['id']) if _buttons(call)]
    return alert


async def test_stranger_alert_and_allow_in_one_tap(bench: Bench):
    """a stranger writes: the owner gets the text with buttons; "Allow" puts them on the list and unmutes them"""
    await _scene(bench)
    await bench.group_message(GROUP, STRANGER, 'may I post here?')
    alert = await _alert(bench)
    assert 'may I post here?' in alert.text and '@stranger' in alert.text, alert.text
    allow = next(b for b in _buttons(alert) if b['data'] and b['data']['tp'] == 'qa' and b['data']['d'] == 0)

    bench.telegram.calls.clear()
    await bench.tap(OWNER, json.dumps(allow['data']))
    [entry] = await bench.sql('SELECT user_service_id, nickname, expires_at FROM allowed_users')
    assert entry == {'user_service_id': str(STRANGER['id']), 'nickname': 'stranger', 'expires_at': None}, entry
    [unmuted] = bench.telegram.calls_of('restrictChatMember')
    assert unmuted.permissions.can_send_messages is True
    [edited] = bench.telegram.calls_of('editMessageText')
    assert any(b['data'] and b['data']['tp'] == 'qu' for b in _buttons(edited)), _buttons(edited)

    bench.telegram.calls.clear()
    await bench.group_message(GROUP, STRANGER, 'thanks')
    assert not _deleted(bench)


async def test_alert_undo(bench: Bench):
    """"Undo" under the result takes the member off the list again"""
    await _scene(bench)
    await bench.group_message(GROUP, STRANGER)
    allow = next(b for b in _buttons(await _alert(bench)) if b['data'] and b['data']['tp'] == 'qa')
    await bench.tap(OWNER, json.dumps(allow['data']))
    [edited] = bench.telegram.calls_of('editMessageText')
    undo = next(b for b in _buttons(edited) if b['data']['tp'] == 'qu')
    await bench.tap(OWNER, json.dumps(undo['data']))
    assert await bench.sql('SELECT * FROM allowed_users') == []


async def test_timed_allow_needs_paid_tariff(bench: Bench):
    """"For 7 days" on the free tariff says it is a paid feature and allows nobody"""
    await _scene(bench)
    await bench.group_message(GROUP, STRANGER)
    week = next(b for b in _buttons(await _alert(bench)) if b['data'] and b['data'].get('d') == 7)
    await bench.tap(OWNER, json.dumps(week['data']))
    assert await bench.sql('SELECT * FROM allowed_users') == []
    [answer] = bench.telegram.calls_of('answerCallbackQuery')
    assert answer.text == localization.get_message(['alerts', 'paid_only'], 'ru')


async def test_timed_allow_on_paid_tariff(bench: Bench):
    """"For 7 days" on a paid tariff gives access that ends in a week"""
    await _scene(bench, paid=True)
    await bench.group_message(GROUP, STRANGER)
    week = next(b for b in _buttons(await _alert(bench)) if b['data'] and b['data'].get('d') == 7)
    await bench.tap(OWNER, json.dumps(week['data']))
    [entry] = await bench.sql('SELECT expires_at FROM allowed_users')
    left = entry['expires_at'] - datetime.datetime.now()
    assert datetime.timedelta(days=6, hours=23) < left <= datetime.timedelta(days=7), left


async def test_one_alert_per_member_a_day(bench: Bench):
    """a stranger writing three times makes one alert"""
    await _scene(bench)
    for _ in range(3):
        await bench.group_message(GROUP, STRANGER)
    assert len([call for call in bench.telegram.sent_to(OWNER['id']) if _buttons(call)]) == 1


async def test_mute_alerts(bench: Bench):
    """"Mute" turns the group's alerts off: the next stranger makes no alert"""
    await _scene(bench)
    await bench.group_message(GROUP, STRANGER)
    mute = next(b for b in _buttons(await _alert(bench)) if b['data'] and b['data']['tp'] == 'qm')
    await bench.tap(OWNER, json.dumps(mute['data']))
    [chat] = await bench.sql('SELECT owner_alerts FROM moderated_chats')
    assert chat['owner_alerts'] is False

    bench.telegram.calls.clear()
    await bench.group_message(GROUP, person(702, 'another'))
    assert not bench.telegram.sent_to(OWNER['id'])


async def test_alert_buttons_only_for_managers(bench: Bench):
    """someone who does not manage the group cannot use its buttons"""
    await _scene(bench)
    await bench.owner(ADMIN)
    await bench.group_message(GROUP, STRANGER)
    allow = next(b for b in _buttons(await _alert(bench)) if b['data'] and b['data']['tp'] == 'qa')
    await bench.tap(ADMIN, json.dumps(allow['data']))
    assert await bench.sql('SELECT * FROM allowed_users') == []


async def test_expiry_reminders(bench: Bench):
    """a day before a timed access ends the owner is reminded once, and told once when it has ended"""
    from pkg.service.member_alerts import MemberAlerts

    _, chat = await _scene(bench, paid=True)
    await bench.whitelist(chat, 'Alice')
    await bench.sql("UPDATE allowed_users SET expires_at = LOCALTIMESTAMP + interval '12 hours'")
    await MemberAlerts.expiry_round()
    await MemberAlerts.expiry_round()
    soon = localization.get_message(['alerts', 'expiry', 'soon'], 'ru', member='@Alice', chat_name='x', date='')
    texts = bench.telegram.texts_to(OWNER['id'])
    assert len(texts) == 1 and soon.split('@Alice')[0] in texts[0], texts

    await bench.sql("UPDATE allowed_users SET expires_at = LOCALTIMESTAMP - interval '1 minute'")
    await MemberAlerts.expiry_round()
    await MemberAlerts.expiry_round()
    assert len(bench.telegram.texts_to(OWNER['id'])) == 2


# Commands in the group

def _reply_to(user: dict, text: str = 'hello') -> dict:
    return {'reply_to_message': {
        'message_id': 9999, 'date': int(datetime.datetime.now().timestamp()),
        'chat': {'id': GROUP, 'type': 'supergroup', 'title': 'Group'}, 'from': user, 'text': text}}


async def test_allow_in_reply(bench: Bench):
    """the owner replies /allow to a stranger: they are on the list by id, the command is deleted, only the owner
    sees the answer"""
    await _scene(bench)
    command = await bench.group_message(GROUP, OWNER, '/allow', **_reply_to(STRANGER))
    [entry] = await bench.sql('SELECT user_service_id, nickname FROM allowed_users')
    assert entry == {'user_service_id': str(STRANGER['id']), 'nickname': 'stranger'}
    assert _deleted(bench) == [command['message_id']]
    [answer] = bench.telegram.sent_to(GROUP)
    assert answer.ephemeral_message_parameters.receiver_user_id == OWNER['id']


async def test_allow_by_nickname_for_a_term(bench: Bench):
    """/allow @nick 7d on a paid tariff gives a week; /deny @nick takes it back"""
    await _scene(bench, paid=True)
    await bench.group_message(GROUP, OWNER, '/allow @anna 7d')
    [entry] = await bench.sql('SELECT nickname, expires_at FROM allowed_users')
    assert entry['nickname'] == 'anna' and entry['expires_at'] is not None
    await bench.group_message(GROUP, OWNER, '/deny @anna')
    assert await bench.sql('SELECT * FROM allowed_users') == []


async def test_allow_from_a_member_is_ignored(bench: Bench):
    """a member who is not an admin sends /allow: nobody is allowed, their message goes like any other"""
    await _scene(bench)
    bench.telegram.members[(GROUP, STRANGER['id'])] = member(STRANGER)
    command = await bench.group_message(GROUP, STRANGER, '/allow @stranger')
    assert await bench.sql('SELECT * FROM allowed_users') == []
    assert _deleted(bench) == [command['message_id']]


async def test_settings_opens_the_page_in_private(bench: Bench):
    """/settings in the group sends the group's page to the owner's private chat"""
    await _scene(bench)
    await bench.group_message(GROUP, OWNER, '/settings')
    texts = bench.telegram.texts_to(OWNER['id'])
    assert any(f'Group {GROUP}' in text for text in texts), texts
    [answer] = bench.telegram.sent_to(GROUP)
    assert answer.text == localization.get_message(['group', 'settings_sent'], 'ru')


async def test_settings_connects_a_new_group(bench: Bench):
    """/settings in a group the bot administers but nobody connected: it is connected to the one who asked"""
    owner = await bench.owner(OWNER)
    bench.group_in_telegram(GROUP, owner)
    await bench.group_message(GROUP, OWNER, '/settings')
    [chat] = await bench.sql('SELECT service_id FROM moderated_chats')
    assert chat['service_id'] == str(GROUP)


async def test_made_admin_connects_the_group(bench: Bench):
    """the owner makes the bot an admin of a group: it is connected and its page arrives in private"""
    owner = await bench.owner(OWNER)
    bench.group_in_telegram(GROUP, owner)
    now = int(datetime.datetime.now().timestamp())
    await bench.feed({'my_chat_member': {
        'chat': {'id': GROUP, 'type': 'supergroup', 'title': f'Group {GROUP}'}, 'from': OWNER, 'date': now,
        'old_chat_member': member(BOT_USER), 'new_chat_member': administrator(BOT_USER)}})
    [chat] = await bench.sql('SELECT service_id FROM moderated_chats')
    assert chat['service_id'] == str(GROUP)
    texts = bench.telegram.texts_to(OWNER['id'])
    assert texts[0] == localization.get_message(['group', 'auto_connected'], 'ru', chat_name=f'Group {GROUP}')
    assert any('Модерация включена' in text for text in texts), texts


async def test_added_without_rights_asks_for_them(bench: Bench):
    """added as a plain member, the bot tells the owner which rights it needs and connects nothing"""
    owner = await bench.owner(OWNER)
    bench.group_in_telegram(GROUP, owner)
    bench.telegram.members[(GROUP, BOT_ID)] = member(BOT_USER)
    now = int(datetime.datetime.now().timestamp())
    await bench.feed({'my_chat_member': {
        'chat': {'id': GROUP, 'type': 'supergroup', 'title': 'Ads'}, 'from': OWNER, 'date': now,
        'old_chat_member': {'status': 'left', 'user': BOT_USER}, 'new_chat_member': member(BOT_USER)}})
    assert await bench.sql('SELECT * FROM moderated_chats') == []
    [told] = bench.telegram.sent_to(OWNER['id'])
    assert told.text == localization.get_message(['group', 'needs_admin'], 'ru', chat_name='Ads')
    [button] = [b for row in told.reply_markup.inline_keyboard for b in row]
    assert 'startgroup=connect&admin=delete_messages+restrict_members+pin_messages' in button.url


async def test_select_a_group_adds_the_bot_with_rights_and_shows_one_page(bench: Bench):
    """/add_chat: "Select a group" asks Telegram to add the bot with its rights in any group the owner runs;
    the bot then gets my_chat_member and chat_shared, and the owner gets one "connected" and one page"""
    owner = await bench.owner(OWNER)
    await bench.private_message(OWNER, '/add_chat')
    [keyboard] = [call.reply_markup for call in bench.telegram.sent_to(OWNER['id'])
                  if getattr(call.reply_markup, 'keyboard', None)]
    request = keyboard.keyboard[0][0].request_chat
    assert request.chat_is_channel is False and not request.bot_is_member
    rights = request.bot_administrator_rights
    assert rights.can_delete_messages and rights.can_restrict_members and rights.can_pin_messages
    assert not rights.can_promote_members and request.user_administrator_rights.can_promote_members

    bench.telegram.calls.clear()
    bench.group_in_telegram(GROUP, owner)
    now = int(datetime.datetime.now().timestamp())
    await bench.feed({'my_chat_member': {
        'chat': {'id': GROUP, 'type': 'supergroup', 'title': f'Group {GROUP}'}, 'from': OWNER, 'date': now,
        'old_chat_member': {'status': 'left', 'user': BOT_USER}, 'new_chat_member': administrator(BOT_USER)}})
    await bench.private_message(OWNER, None, chat_shared={'request_id': 1, 'chat_id': GROUP})
    connected = localization.get_message(['group', 'auto_connected'], 'ru', chat_name=f'Group {GROUP}')
    texts = bench.telegram.texts_to(OWNER['id'])
    assert texts.count(connected) == 1, texts
    assert len([text for text in texts if 'Модерация включена' in text]) == 1, texts
    assert len(await bench.sql('SELECT * FROM moderated_chats')) == 1


# The group page in private

async def _open_page(bench: Bench, chat: dict):
    await bench.private_message(OWNER, f"/start chat_{chat['id']}")
    return [call for call in bench.telegram.sent_to(OWNER['id']) if _buttons(call)][-1]


async def test_page_by_deep_link(bench: Bench):
    """/start chat_<id> opens the group's page with its state and settings"""
    _, chat = await _scene(bench)
    page = await _open_page(bench, chat)
    assert 'Модерация включена' in page.text and 'Удалено за 7 дней: 0' in page.text, page.text
    kinds = {b['data']['tp'] for b in _buttons(page)}
    assert {'add_to_chat_whitelist', 'chat_whitelist', 'switch_mode', 'chat_post_limit', 'chat_access', 'switch_admins'} <= kinds


def _shown(bench: Bench):
    """The last page shown to the owner, sent or edited in place."""
    return [call for call in bench.telegram.calls_of('sendMessage', 'editMessageText')
            if int(call.chat_id or 0) == OWNER['id']][-1]


async def _limit_row(bench: Bench) -> dict:
    [row] = await bench.sql('SELECT post_limit, post_limit_hours FROM moderated_chats')
    return dict(row)


async def test_page_switch_mode_and_limit(bench: Bench):
    """on a paid tariff: "who writes" switches to everyone; the limit page takes a button, words, "выкл",
    and says what is wrong with nonsense"""
    _, chat = await _scene(bench, paid=True)
    await _open_page(bench, chat)
    await bench.tap(OWNER, json.dumps({'tp': 'switch_mode'}))
    await bench.tap(OWNER, json.dumps({'tp': 'chat_post_limit'}))
    page = _shown(bench)
    assert 'Лимит постов' in page.text and 'без лимита' in page.text and 'платном' not in page.text, page.text
    assert '3 в день' in [b['text'] for b in _buttons(page)]
    await bench.tap(OWNER, json.dumps({'tp': 'lim_set', 'n': 3, 'h': 24}))
    [row] = await bench.sql('SELECT everyone_can_write FROM moderated_chats')
    assert row['everyone_can_write'] is True
    assert await _limit_row(bench) == {'post_limit': 3, 'post_limit_hours': 24}
    assert '• 3 в день' in [b['text'] for b in _buttons(_shown(bench))]

    await bench.private_message(OWNER, '10 за 2 дня')
    assert await _limit_row(bench) == {'post_limit': 10, 'post_limit_hours': 48}
    assert 'Сохранено: 10 за 2 дня' in _shown(bench).text
    await bench.private_message(OWNER, 'много')
    assert 'Не похоже на лимит' in _shown(bench).text
    assert await _limit_row(bench) == {'post_limit': 10, 'post_limit_hours': 48}
    await bench.private_message(OWNER, 'выкл')
    assert await _limit_row(bench) == {'post_limit': None, 'post_limit_hours': None}


async def test_page_check_admins_too(bench: Bench):
    """"Admins: checked too": the owner's own message off the whitelist goes, the page says nobody can write;
    switched back, the owner writes again"""
    _, chat = await _scene(bench)
    await bench.group_message(GROUP, OWNER, 'mine stays')
    assert not _deleted(bench)
    await _open_page(bench, chat)
    await bench.tap(OWNER, json.dumps({'tp': 'switch_admins'}))
    [row] = await bench.sql('SELECT allow_administrators FROM moderated_chats')
    assert row['allow_administrators'] is False
    assert 'Ваши тоже' in bench.telegram.calls_of('answerCallbackQuery')[-1].text
    page = _shown(bench)
    assert 'админы тоже проверяются' in page.text and 'даже вы' in page.text, page.text
    assert '👮 Админы: тоже проверять' in [b['text'] for b in _buttons(page)]

    bench.telegram.calls.clear()
    gone = await bench.group_message(GROUP, OWNER, 'mine goes')
    assert _deleted(bench) == [gone['message_id']]
    await bench.tap(OWNER, json.dumps({'tp': 'switch_admins'}))
    bench.telegram.calls.clear()
    await bench.group_message(GROUP, OWNER, 'mine stays again')
    assert not _deleted(bench)


async def test_page_limit_is_paid(bench: Bench):
    """on the free tariff the limit page says it works on a paid one; set now, it waits for the tariff"""
    _, chat = await _scene(bench)
    await _open_page(bench, chat)
    await bench.tap(OWNER, json.dumps({'tp': 'chat_post_limit'}))
    assert 'Работает на платном тарифе' in _shown(bench).text
    await bench.tap(OWNER, json.dumps({'tp': 'lim_set', 'n': 1, 'h': 24}))
    assert await _limit_row(bench) == {'post_limit': 1, 'post_limit_hours': 24}


async def test_page_arrows_between_groups(bench: Bench):
    """with two groups, ▶️ on one page opens the other"""
    owner, chat = await _scene(bench, paid=True)
    other = await bench.group(OTHER_GROUP, owner)
    page = await _open_page(bench, chat)
    forward = next(b for b in _buttons(page) if b['text'] == '▶️')
    assert forward['data'] == {'tp': 'switch', 'id': other['id']}
    bench.telegram.calls.clear()
    await bench.tap(OWNER, json.dumps(forward['data']))
    assert any(f'Group {OTHER_GROUP}' in text for text in _private_texts(bench, OWNER)), bench.telegram.calls


async def test_add_members_from_private(bench: Bench):
    """on the "allow members" screen, a message with a nickname, an id and a term puts both on the list for 7 days"""
    _, chat = await _scene(bench, paid=True)
    await _open_page(bench, chat)
    await bench.tap(OWNER, json.dumps({'tp': 'add_to_chat_whitelist'}))
    await bench.private_message(OWNER, '@anna 123456789 7d')
    rows = await bench.sql('SELECT nickname, user_service_id, expires_at IS NOT NULL AS timed FROM allowed_users '
                           'ORDER BY id')
    assert rows == [{'nickname': 'anna', 'user_service_id': None, 'timed': True},
                    {'nickname': None, 'user_service_id': '123456789', 'timed': True}], rows


async def test_add_members_picked_from_contacts(bench: Bench):
    """members picked with the contacts button are added by id"""
    _, chat = await _scene(bench)
    await _open_page(bench, chat)
    await bench.tap(OWNER, json.dumps({'tp': 'add_to_chat_whitelist'}))
    await bench.private_message(OWNER, None, users_shared={'request_id': 2, 'users': [
        {'user_id': 801, 'username': 'bob', 'first_name': 'Bob'}]})
    [row] = await bench.sql('SELECT nickname, user_service_id, display_name FROM allowed_users')
    assert row == {'nickname': 'bob', 'user_service_id': '801', 'display_name': 'Bob'}, row


# The bot's admins

async def test_users_count_for_a_group_owner(bench: Bench):
    """/usersCount for a group owner: their groups with members, whitelist and removed messages, nothing of the bot"""
    await bench.private_message(STRANGER, '/stats')
    assert 'No groups yet' in bench.telegram.texts_to(STRANGER['id'])[-1]

    owner, chat = await _scene(bench, paid=True)
    bench.telegram.answers['getChatMemberCount'] = 1234
    await bench.sql("INSERT INTO allowed_users (moderated_chat_id, nickname, expires_at, created_at, updated_at) "
                    "VALUES ($1, 'anna', NULL, NOW(), NOW()), ($1, 'bob', NOW() + interval '7 days', NOW(), NOW()), "
                    "($1, 'old', NOW() - interval '1 day', NOW(), NOW())", chat['id'])
    await bench.sql("INSERT INTO moderated_chat_statistics (moderated_chat_id, deleted_messages_count, day, "
                    "created_at, updated_at) VALUES ($1, 5, CURRENT_DATE, NOW(), NOW()), "
                    "($1, 7, CURRENT_DATE - 3, NOW(), NOW()), ($1, 100, CURRENT_DATE - 20, NOW(), NOW())", chat['id'])
    bench.telegram.calls.clear()
    await bench.private_message(OWNER, '/usersCount')
    [stats] = bench.telegram.texts_to(OWNER['id'])
    assert 'Ваши группы: 1' in stats and 'Участников всего: 1 234' in stats, stats
    assert 'В белых списках: 2 (на срок: 1)' in stats, stats
    assert 'сегодня 5, за 7 дней 12, за 30 дней 112' in stats, stats
    assert f'Group {GROUP}' in stats or 'Модерация включена' in stats, stats
    assert 'Пользователи' not in stats and 'Деньги' not in stats, stats
    # The summary in sight, the groups behind a tap
    assert stats.index('за 30 дней 112') < stats.index('<blockquote expandable><b>'), stats


async def test_users_count_extended_for_the_bot_owner(bench: Bench):
    """/usersCount for the bot's owner: the whole bot (users, groups, money), then their own groups"""
    owner, _ = await _scene(bench)
    bench.telegram.answers['getChatMemberCount'] = 10
    await bench.sql('UPDATE users SET is_admin = TRUE')
    await bench.private_message(OWNER, '/usersCount')
    [stats] = bench.telegram.texts_to(OWNER['id'])
    assert 'Всего: 1' in stats and 'Модерируются: 1' in stats and 'Деньги' in stats, stats
    assert stats.index('Деньги') < stats.index('<blockquote expandable>📊 <b>Ваши группы: 1'), stats
    assert stats.endswith('</blockquote>') and stats.count('<blockquote') == 1, stats


async def test_command_menus(bench: Bench):
    """the menus: private commands (/stats among them) for everyone, group commands for group admins, /usersCount
    in none of them"""
    import re
    from pkg.service.bot_commands import set_bot_commands

    await bench.owner(OWNER)
    bench.telegram.answers['getChatMemberCount'] = 3
    bench.telegram.calls.clear()
    await set_bot_commands(bench.bot)

    menus = {(call.scope.type, getattr(call.scope, 'chat_id', None), call.language_code):
             {c.command: c.description for c in call.commands} for call in bench.telegram.calls_of('setMyCommands')}
    assert set(menus[('all_private_chats', None, 'ru')]) == {
        'menu', 'my_chats', 'stats', 'add_chat', 'subscription', 'settings', 'access', 'help'}
    assert menus[('all_private_chats', None, None)]['my_chats'] == 'My groups'
    assert set(menus[('all_chat_administrators', None, 'ru')]) == {'allow', 'deny', 'settings'}
    assert not any(scope == 'chat' or 'userscount' in menu for (scope, _, _), menu in menus.items())
    for menu in menus.values():
        for command, description in menu.items():
            assert re.fullmatch(r'[a-z0-9_]{1,32}', command) and 0 < len(description) <= 256, (command, description)
    assert {call.scope.type for call in bench.telegram.calls_of('deleteMyCommands')} == {'default'}

    # Every command in the private menu leads somewhere
    for command in menus[('all_private_chats', None, 'ru')]:
        bench.telegram.calls.clear()
        await bench.private_message(OWNER, f'/{command}')
        assert bench.telegram.calls_of('sendMessage') or bench.telegram.calls_of('sendPhoto') or \
            bench.telegram.calls_of('editMessageText'), command


async def test_allow_result_names_the_group(bench: Bench):
    """the result of "Allow" names the group even when its title was never saved"""
    await _scene(bench)
    await bench.sql('UPDATE moderated_chats SET name = NULL')
    await bench.group_message(GROUP, STRANGER)
    allow = next(b for b in _buttons(await _alert(bench)) if b['data'] and b['data']['tp'] == 'qa')
    await bench.tap(OWNER, json.dumps(allow['data']))
    [edited] = bench.telegram.calls_of('editMessageText')
    assert f'Group {GROUP}' in edited.text, edited.text


async def test_help_is_html(bench: Bench):
    """/help is sent as HTML (its text has bold headings)"""
    await bench.owner(OWNER)
    await bench.private_message(OWNER, '/help')
    [page] = [call for call in bench.telegram.sent_to(OWNER['id']) if '<b>' in (call.text or '')]
    assert page.parse_mode == 'HTML'


async def test_select_a_group_chat_shared_first(bench: Bench):
    """the other order: chat_shared before my_chat_member, still one "connected" and one page"""
    owner = await bench.owner(OWNER)
    await bench.private_message(OWNER, '/add_chat')
    bench.telegram.calls.clear()
    bench.group_in_telegram(GROUP, owner)
    await bench.private_message(OWNER, None, chat_shared={'request_id': 1, 'chat_id': GROUP})
    now = int(datetime.datetime.now().timestamp())
    await bench.feed({'my_chat_member': {
        'chat': {'id': GROUP, 'type': 'supergroup', 'title': f'Group {GROUP}'}, 'from': OWNER, 'date': now,
        'old_chat_member': {'status': 'left', 'user': BOT_USER}, 'new_chat_member': administrator(BOT_USER)}})
    texts = bench.telegram.texts_to(OWNER['id'])
    assert len([text for text in texts if 'подключена' in text]) == 1, texts
    assert len([text for text in texts if 'Модерация включена' in text]) == 1, texts


async def test_add_group_from_the_menu_button(bench: Bench):
    """"Add a group" in the menu (a button, so the menu message is edited): the keyboard under the input comes
    as a new message, it cannot be edited in"""
    await bench.owner(OWNER)
    await bench.private_message(OWNER, '/menu')
    menu = [call for call in bench.telegram.sent_to(OWNER['id']) if _buttons(call)][-1]
    add = next(b for b in _buttons(menu) if 'Добавить группу' in b['text'])
    bench.telegram.calls.clear()
    await bench.tap(OWNER, json.dumps(add['data']))
    keyboards = [call for call in bench.telegram.sent_to(OWNER['id'])
                 if getattr(call.reply_markup, 'keyboard', None)]
    assert len(keyboards) == 1 and keyboards[0].reply_markup.keyboard[0][0].request_chat, bench.telegram.calls
