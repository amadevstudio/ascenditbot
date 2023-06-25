from framework.controller.message_tools import message_sender, go_back_inline_markup, chat_id_sender
from framework.controller.types import ControllerParams
from lib.language import localization
from pkg.service.tariff import Tariff
from pkg.service.user import User
from pkg.template.tariff.common import build_subscription_info_short
from project.types import UserInterface


async def start(params: ControllerParams):
    call, message = params['call'], params['message']

    registration_result = None

    if call is None:
        await message.reply('👋')
        initial_data = User.analyze_initial_data(message.text)
        registration_result = await User.register(message.chat.id, params['language_code'], initial_data)

    markup = [[{
        'text': localization.get_message(['welcome', 'lets_begin'], params['language_code']),
        'callback_data': {'tp': 'menu'}}]]

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
    markup = [[buttons[0], buttons[1]], [buttons[2], buttons[3]], [buttons[4]]]

    answer_messages = []

    user_id = await User.get_id_by_service_id(message.chat.id)

    user_tariff_info = await Tariff.user_tariff_info(user_id)

    trial_info = await Tariff.activate_trial(user_tariff_info)
    if trial_info is not None:
        answer_messages.append({
            'type': 'text',
            'text': localization.get_message(['subscription', 'free_trial'], params['language_code']),
            'parse_mode': 'HTML'
        })
        user_tariff_info = await Tariff.user_tariff_info(user_id)

    answer_messages.append({
        'type': 'text',
        'text':
            build_subscription_info_short(user_tariff_info, params['language_code'])
            + "\n\n" + localization.get_message(['menu', 'text'], params['language_code']),
        'reply_markup': markup,
        'parse_mode': 'HTML'
    })

    await message_sender(message.chat.id, message_structures=answer_messages)


async def help_page(params: ControllerParams):
    call, message = params['call'], params['message']

    await message_sender(message.chat.id, message_structures=[{
        'type': 'text',
        'text': localization.get_message(['help', 'text'], params['language_code']),
        'reply_markup': go_back_inline_markup(params['language_code'])
    }])
