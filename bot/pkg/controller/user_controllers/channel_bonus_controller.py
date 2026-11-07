"""🎁 +15 days for subscribing to the bot owner's channels (pkg/service/channel_bonus.py), from the menu or /bonus."""
import html

from framework.controller.message_tools import message_sender, notify, go_back_inline_markup
from framework.controller.types import ControllerParams
from lib.language import localization
from pkg.service.channel_bonus import BONUS_DAYS, ChannelBonus
from pkg.service.user import User


def channel_names(channels: list[dict]) -> str:
    return ', '.join(f"<b>{html.escape(c['title'] or c['service_id'])}</b>" for c in channels)


def channel_buttons(channels: list[dict]) -> list[list[dict]]:
    return [[{'text': '📣 ' + (c['title'] or c['service_id']), 'url': c['link']}] for c in channels if c['link']]


async def page(params: ControllerParams, done: str | None = None, end_date=None):
    message, language_code = params['message'], params['language_code']

    def text(*path, **kwargs) -> str:
        return localization.get_message(['bonus', *path], language_code, **kwargs)

    user_id = await User.get_id_by_service_id(message.chat.id)
    claim = await ChannelBonus.claim(user_id)
    channels = await ChannelBonus.channels()
    markup = []
    if done == 'granted':
        body = text('granted', days=BONUS_DAYS, date=end_date.strftime('%d.%m.%Y'))
    elif done == 'restored':
        body = text('restored')
    elif claim is not None and claim['lost_at'] is not None:
        mine = [c for c in channels if c['service_id'] in claim['channel_ids']]
        body = text('lost', channels=channel_names(mine))
        markup = [*channel_buttons(mine), [{'text': text('check_button'), 'callback_data': {'tp': 'bonus_check'}}]]
    elif claim is not None:
        body = text('already')
    elif not channels:
        body = text('none')
    else:
        body = text('offer', days=BONUS_DAYS, channels=channel_names(channels),
                    penalty=ChannelBonus.penalty_days(len(channels)))
        markup = [*channel_buttons(channels), [{'text': text('check_button'), 'callback_data': {'tp': 'bonus_check'}}]]

    await message_sender(message.chat.id, message_structures=[{
        'type': 'text', 'text': body, 'parse_mode': 'HTML', 'disable_web_page_preview': True,
        'reply_markup': [*markup, *go_back_inline_markup(language_code)]}])


async def check(params: ControllerParams):
    """"✅ I subscribed": the bonus (or the free group back), or which channels the bot does not see them in."""
    call, message, language_code = params['call'], params['message'], params['language_code']
    user_id = await User.get_id_by_service_id(message.chat.id)
    result = await ChannelBonus.take(user_id, message.chat.id)
    if 'error' in result:
        await notify(call, message, localization.get_message(
            ['bonus', 'not_subscribed' if result['error'] == 'not_subscribed' else 'none'], language_code,
            channels=', '.join(c['title'] or c['service_id'] for c in result['channels'])), alert=True)
        return
    if call is not None:
        await notify(call, message, localization.get_message(['bonus', 'toast'], language_code))
    await page(params, done=result['result'] if result['result'] != 'already' else None,
               end_date=result.get('end_date'))
