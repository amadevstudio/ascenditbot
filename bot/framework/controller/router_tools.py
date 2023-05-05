import json

from framework.controller.types import ControllerParams
from framework.system import telegram_types

from lib.telegram.aiogram.message_processor import call_and_message_accessed_processor
from pkg.config import routes
from pkg.config.routes import RouteMap, AvailableRoutes

from pkg.service.user_storage import UserStorage


# TODO: put to middleware
def get_type(call: telegram_types.CallbackQuery):
    return json.loads(call.data).get("tp", "")


def message_route_validator(state_types: list[str], message: telegram_types.Message):
    if message.text is not None and message.text[0] == '/':
        return False

    route_map_state_types = [RouteMap.state(state_type) for state_type in state_types]
    return user_state(message) in route_map_state_types


def user_state(entity: telegram_types.Message | telegram_types.CallbackQuery):
    try:
        chat_id = entity.message.chat.id
    except AttributeError:
        chat_id = entity.chat.id
    return UserStorage.curr_state(chat_id)


def construct_params(call, message) -> ControllerParams:
    # TODO: get call data here
    return {
        'call': call,
        'message': message,
        'language_code': call.from_user.language_code if call is not None else message.from_user.language_code,
        # 'call_data': state_data.get_state_data(call, message, current_type)
    }


async def event_wrapper(
        route_type: AvailableRoutes, entity: telegram_types.Message | telegram_types.CallbackQuery,
        *args, **kwargs):
    # Args: manual
    # Kwargs: bot, event_from_user, ...

    call, message = call_and_message_accessed_processor(entity)

    # Validate access
    validator = RouteMap.get_route_prop(route_type, 'validator')
    if validator is not None:
        valid = await validator(call, message)
        if not valid:
            return

    # Clear state on commands
    if call is None and message.text is not None and message.text[0] == '/':
        UserStorage.new_navigation_journey(message.chat.id, routes.RouteMap.type('menu'))

    succeed = await RouteMap.get_route_prop(route_type, 'method')(construct_params(call, message))

    if succeed is not False:
        UserStorage.change_page(message.chat.id, routes.RouteMap.type(route_type))


async def event_action_wrapper(
        route_type: AvailableRoutes, action_type: str, call: telegram_types.CallbackQuery, *args, **kwargs):
    call, message = call_and_message_accessed_processor(call)

    params: ControllerParams = {
        'call': call,
        'message': message,
        'language_code': call.from_user.language_code
    }

    await RouteMap.get_route_action_prop(route_type, action_type, 'method')(construct_params(call, message))
