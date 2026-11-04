"""What the bot does with a message in a moderated group: the product itself."""
import datetime

from aiogram.exceptions import TelegramBadRequest

from lib.language import localization
from tests.bench import Bench, BOT_USER, person

GROUP = -1001000000001
OWNER = person(501, 'owner', 'ru')
ALICE = person(601, 'Alice')
STRANGER = person(701, 'stranger', 'en')
NOTICE_EN = localization.get_message(['work', 'removed_notice', 'text'], 'en')
NOTICE_RU = localization.get_message(['work', 'removed_notice', 'text'], 'ru')
PROMO_EN = localization.get_message(['work', 'removed_notice', 'promo'], 'en')


async def _scene(bench: Bench, **chat_fields):
    owner = await bench.owner(OWNER)
    chat = await bench.group(GROUP, owner, **chat_fields)
    await bench.whitelist(chat, 'Alice')
    return owner, chat


def _untouched(bench: Bench) -> bool:
    return not bench.telegram.calls_of('deleteMessage', 'restrictChatMember', 'sendMessage')


async def test_whitelisted_stays(bench: Bench):
    """a member on the whitelist writes: the message stays, the bot says nothing"""
    await _scene(bench)
    await bench.group_message(GROUP, ALICE)
    assert _untouched(bench), bench.telegram.calls


async def test_whitelist_ignores_case(bench: Bench):
    """the whitelist matches nicknames in any case (Alice on the list, @alice writes)"""
    await _scene(bench)
    await bench.group_message(GROUP, person(602, 'alice'))
    await bench.group_message(GROUP, person(603, 'ALICE'))
    assert _untouched(bench), bench.telegram.calls


async def test_stranger_removed_restricted_told(bench: Bench):
    """a stranger writes in a supergroup: the message goes, they are muted for 5 minutes and told why"""
    await _scene(bench)
    message = await bench.group_message(GROUP, STRANGER, 'buy my course')

    [deleted] = bench.telegram.calls_of('deleteMessage')
    assert (deleted.chat_id, deleted.message_id) == (GROUP, message['message_id'])

    [restricted] = bench.telegram.calls_of('restrictChatMember')
    assert (restricted.chat_id, restricted.user_id) == (GROUP, STRANGER['id'])
    assert restricted.permissions.can_send_messages is False
    muted_for = restricted.until_date - datetime.datetime.now(datetime.timezone.utc)
    assert datetime.timedelta(minutes=4) < muted_for <= datetime.timedelta(minutes=5), muted_for

    [notice] = bench.telegram.sent_to(GROUP)
    assert notice.ephemeral_message_parameters.receiver_user_id == STRANGER['id'], 'only the stranger sees it'
    assert notice.text.startswith(NOTICE_EN)


async def test_restriction_duration_setting(bench: Bench):
    """the mute lasts as long as the owner set for the group"""
    await _scene(bench, restriction_duration_minutes=60)
    await bench.group_message(GROUP, STRANGER)
    [restricted] = bench.telegram.calls_of('restrictChatMember')
    muted_for = restricted.until_date - datetime.datetime.now(datetime.timezone.utc)
    assert datetime.timedelta(minutes=59) < muted_for <= datetime.timedelta(minutes=60), muted_for


async def test_basic_group_not_restricted(bench: Bench):
    """in a basic group (not a supergroup) the message goes but nobody is muted: Telegram cannot restrict there"""
    await _scene(bench)
    await bench.group_message(GROUP, STRANGER, chat_type='group')
    assert len(bench.telegram.calls_of('deleteMessage')) == 1
    assert not bench.telegram.calls_of('restrictChatMember')


async def test_notice_language(bench: Bench):
    """the notice is in the language of the one who wrote, not of the owner"""
    await _scene(bench)
    await bench.group_message(GROUP, person(702, 'ivan', 'ru'))
    await bench.group_message(GROUP, person(703, 'jose', 'es'))
    [ru, other] = bench.telegram.texts_to(GROUP)
    assert ru.startswith(NOTICE_RU)
    assert other.startswith(NOTICE_EN), 'a language the bot does not speak falls back to English'


async def test_free_tariff_notice_promotes(bench: Bench):
    """on the free tariff the notice points to the bot"""
    await _scene(bench)
    await bench.group_message(GROUP, STRANGER)
    [notice] = bench.telegram.texts_to(GROUP)
    assert notice == NOTICE_EN + '\n\n' + PROMO_EN


async def test_paid_tariff_notice_plain(bench: Bench):
    """on a paid tariff the notice has no link to the bot"""
    from pkg.service.tariff import Tariff

    owner, _ = await _scene(bench)
    await Tariff.change(owner['id'], 1, force=True)
    await Tariff.prolong(owner['id'], 30)
    await bench.group_message(GROUP, STRANGER)
    [notice] = bench.telegram.texts_to(GROUP)
    assert notice == NOTICE_EN


async def test_notice_not_repeated(bench: Bench):
    """a stranger who keeps writing loses every message but gets one notice, not one per message"""
    await _scene(bench)
    for _ in range(3):
        await bench.group_message(GROUP, STRANGER)
    assert len(bench.telegram.calls_of('deleteMessage')) == 3
    assert len(bench.telegram.sent_to(GROUP)) == 1


async def test_paused_group_ignored(bench: Bench):
    """a group the owner paused is not moderated"""
    await _scene(bench, active=False)
    await bench.group_message(GROUP, STRANGER)
    assert _untouched(bench), bench.telegram.calls


async def test_disabled_group_ignored(bench: Bench):
    """a group over the tariff's limit (disabled) is not moderated"""
    await _scene(bench, disabled=True)
    await bench.group_message(GROUP, STRANGER)
    assert _untouched(bench), bench.telegram.calls


async def test_unknown_group_ignored(bench: Bench):
    """a group nobody connected is not moderated, even with the bot in it"""
    await bench.group_message(-1009999999999, STRANGER)
    assert _untouched(bench), bench.telegram.calls


async def test_switched_off_member_removed(bench: Bench):
    """a member the owner switched off on the whitelist is treated as a stranger"""
    from pkg.service.allowed_user import AllowedUser

    _, chat = await _scene(bench)
    [alice] = await bench.sql("SELECT id FROM allowed_users WHERE nickname = 'Alice'")
    await AllowedUser.switch_active(alice['id'])
    await bench.group_message(GROUP, ALICE)
    assert len(bench.telegram.calls_of('deleteMessage')) == 1


async def test_bots_and_anonymous_admins_ignored(bench: Bench):
    """messages of bots and of anonymous admins (GroupAnonymousBot) are left alone"""
    await _scene(bench)
    await bench.group_message(GROUP, {**person(801, 'somebot'), 'is_bot': True})
    await bench.group_message(GROUP, {**person(1087968824, 'GroupAnonymousBot'), 'is_bot': True})
    await bench.group_message(GROUP, BOT_USER)
    assert _untouched(bench), bench.telegram.calls


async def test_no_username_removed(bench: Bench):
    """a member without a username cannot be whitelisted, so their message always goes (known gap)"""
    await _scene(bench)
    await bench.group_message(GROUP, person(901))
    assert len(bench.telegram.calls_of('deleteMessage')) == 1


async def test_undeletable_message_left(bench: Bench):
    """when Telegram refuses the deletion nobody is muted or told"""
    await _scene(bench)
    bench.telegram.answers['deleteMessage'] = lambda method: TelegramBadRequest(
        method, "Bad Request: message can't be deleted")
    await bench.group_message(GROUP, STRANGER)
    assert not bench.telegram.calls_of('restrictChatMember', 'sendMessage')


async def test_notice_failure_harmless(bench: Bench):
    """when the notice cannot be sent the message is still removed and the member muted"""
    await _scene(bench)
    bench.telegram.answers['sendMessage'] = lambda method: TelegramBadRequest(
        method, 'Bad Request: method is not available')
    await bench.group_message(GROUP, STRANGER)
    assert len(bench.telegram.calls_of('deleteMessage')) == 1
    assert len(bench.telegram.calls_of('restrictChatMember')) == 1
