import datetime
import html

from framework.controller.message_tools import message_sender, go_back_inline_markup, chat_id_sender
from framework.controller.types import ControllerParams
from pkg.controller.user_controllers import chats_controller
from pkg.service.channel_bonus import ChannelBonus
from pkg.service.chat import Chat
from lib.language import localization
from pkg.service.tariff import Tariff
from pkg.service.user import User
from pkg.template.tariff.common import build_subscription_info_short
from project.i18n_owner_tools import guide_url
from project.types import UserInterface


def guide_button(language_code: str | None) -> dict:
    """How it all works, with screenshots: the guide in the bot's channel."""
    return {'text': localization.get_message(['help', 'guide_button'], language_code), 'url': guide_url(language_code)}


async def start(params: ControllerParams):
    call, message = params['call'], params['message']

    registration_result = None

    if call is None:
        initial_data = User.analyze_initial_data(message.text)
        registration_result = await User.register(message.chat.id, params['language_code'], initial_data)

        # A link from a group (/settings there, an alert): straight to that group's page
        chat_id = str(initial_data.get('chat') or '')
        if chat_id.isdigit() and await chats_controller.open_chat_page(message, int(chat_id), params['language_code']):
            return False

        # The way in through the bot (j_<group id>): the group's page for someone who wants to write there
        join_id = str(initial_data.get('j') or '')
        if join_id.isdigit():
            from pkg.controller.routers.access_router import open_join_page
            await open_join_page(message, int(join_id), params['language_code'])
            return False

        await message.reply('👋')

    markup = [[{
        'text': localization.get_message(['welcome', 'lets_begin'], params['language_code']),
        'callback_data': {'tp': 'menu'}}], [guide_button(params['language_code'])]]

    message_structures = [{
        'type': 'text',
        'text': localization.get_message(['welcome', 'introduction'], params['language_code']),
        'reply_markup': markup,
    }]
    await message_sender(message.chat.id, message_structures=message_structures)

    if registration_result is not None and registration_result.get('refer', None) is not None:
        refer: UserInterface = registration_result['refer']
        await chat_id_sender(int(refer['service_id']), [{
            'type': 'text',
            'text': localization.get_message(
                ['subscription', 'fund', 'from_referral', 'initialed'], refer['language_code']),
        }])


async def menu(params: ControllerParams):
    call, message = params['call'], params['message']

    buttons = []
    for button_type in ['add_chat', 'my_chats', 'help', 'subscription', 'settings']:
        buttons.append({
            'text': localization.get_message(['buttons', button_type], params['language_code']),
            'callback_data': {'tp': button_type}})
    markup = [[buttons[0], buttons[1]], [buttons[2], buttons[3]], [buttons[4], guide_button(params['language_code'])]]

    answer_messages = []

    user_id = await User.get_id_by_service_id(message.chat.id)

    user_tariff_info = await Tariff.user_tariff_info(user_id)

    trial_info = await Tariff.activate_trial(user_tariff_info)
    if trial_info is not None:
        user_tariff_info = await Tariff.user_tariff_info(user_id)
        end_date = user_tariff_info['end_date']
        answer_messages.append({
            'type': 'text',
            'text': localization.get_message(
                ['subscription', 'free_trial'], params['language_code'],
                days=(end_date - datetime.datetime.now()).days + 1 if end_date is not None else 15,
                groups=user_tariff_info['channels_count'] or 3),
            'parse_mode': 'HTML'
        })

    # Someone with no group yet: where to start
    menu_text = localization.get_message(['menu', 'text'], params['language_code'])
    if not await Chat.data_count_provider(user_id):
        menu_text += "\n\n" + localization.get_message(['menu', 'start_hint'], params['language_code'])
    else:
        # Groups that are on but where the bot cannot delete: nothing is moderated there, and the page looks fine
        blocked = await Chat.working_groups_without_rights(user_id)
        if blocked:
            names = ', '.join(f"<b>{html.escape(chat['name'] or str(chat['service_id']))}</b>" for chat in blocked)
            menu_text += "\n\n" + localization.get_message(
                ['menu', 'no_rights', 'one' if len(blocked) == 1 else 'many'], params['language_code'], chats=names)

    # +15 days for subscribing to the bot's channels, or the free group back after unsubscribing
    bonus_state = await ChannelBonus.state(user_id)
    if bonus_state is not None:
        if bonus_state == 'lost':
            menu_text += "\n\n" + localization.get_message(['bonus', 'menu_lost'], params['language_code'])
        markup.append([{'text': localization.get_message(['bonus', 'menu_button', bonus_state], params['language_code']),
                        'callback_data': {'tp': 'bonus'}}])

    answer_messages.append({
        'type': 'text',
        'text': build_subscription_info_short(user_tariff_info, params['language_code']) + "\n\n" + menu_text,
        'reply_markup': markup,
        'parse_mode': 'HTML'
    })

    await message_sender(message.chat.id, message_structures=answer_messages)


SUPPORT_URL = 'https://t.me/ascendit_channel?direct'


async def help_page(params: ControllerParams):
    call, message = params['call'], params['message']

    await message_sender(message.chat.id, message_structures=[{
        'type': 'text',
        'text': localization.get_message(['help', 'text'], params['language_code']),
        # Questions go to the direct messages of the bot's channel
        'reply_markup': [[guide_button(params['language_code'])],
                         [{'text': localization.get_message(['help', 'contact_button'], params['language_code']),
                           'url': SUPPORT_URL}], *go_back_inline_markup(params['language_code'])],
        'parse_mode': 'HTML',
        'disable_web_page_preview': True
    }])

async def privacy(params: ControllerParams):
    call, message = params['call'], params['message']

    await message_sender(message.chat.id, message_structures=[{
        'type': 'text',
        'text': localization.get_message(['help', 'privacy'], params['language_code']),
        'reply_markup': go_back_inline_markup(params['language_code'])
    }])
