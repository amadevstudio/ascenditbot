from framework.system import telegram_types

from framework.controller import state_data
from pkg.controller.user_controllers.common_controller import chat_access_denied
from pkg.service.chat import Chat


async def chat_access_validator(call: telegram_types.CallbackQuery, message: telegram_types.Message) -> bool:
    channel_state_data = state_data.get_state_data(call, message, 'chat')
    chat_service_id = channel_state_data.get(
        'service_id',
        Chat.find(channel_state_data['id']).get('service_id', None))

    if chat_service_id is None:
        validate_result = {'error': 'not_found'}
    else:
        validate_result = await Chat.validate_access(chat_service_id, message.chat.id)

    if 'error' in validate_result:
        await chat_access_denied(call, message, validate_result)
        return False

    return True
