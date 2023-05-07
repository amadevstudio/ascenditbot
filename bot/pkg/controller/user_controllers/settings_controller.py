from framework.controller.types import ControllerParams

from framework.controller.message_tools import message_sender, go_back_inline_markup, go_back_inline_button, \
    is_call_or_command
from lib.language import localization
from pkg.config import routes
from pkg.service.user import User


async def page(params: ControllerParams):
    call, message = params['call'], params['message']

    reply_markup = [[{
        'text': localization.get_message(['settings', 'buttons', 'email'], params['language_code']),
        'callback_data': {'tp': routes.RouteMap.type('settings_email')}}],
        [go_back_inline_button(params['language_code'])]]

    message_structures = [{
        'type': 'text',
        'text': localization.get_message(['settings', 'page'], params['language_code']),
        'reply_markup': reply_markup,
    }]
    await message_sender(message.chat.id, message_structures=message_structures)


async def email(params: ControllerParams):
    call, message = params['call'], params['message']

    if not is_call_or_command(call, message) and len(message.text) != 0:
        User.update_email_by_service_id(message.chat.id, message.text)

    user = User.find_by_service_id(message.chat.id)

    message_structures = [{
        'type': 'text',
        'text': localization.get_message(
            ['settings', 'email', 'page'], params['language_code'],
            email=user['email'] if user['email'] is not None else localization.get_message(
                ['settings', 'email', 'empty'], params['language_code']
            )),
        'reply_markup': go_back_inline_markup(params['language_code']),
    }]
    await message_sender(message.chat.id, message_structures=message_structures)
