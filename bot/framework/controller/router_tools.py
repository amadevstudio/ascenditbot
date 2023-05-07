import json

from framework.controller import state_data, state_navigator, message_tools
from framework.controller.types import ControllerParams

from framework.system import telegram_types

from lib.telegram.aiogram.message_processor import call_and_message_accessed_processor
from pkg.config.routes import RouteMap
from pkg.config.routes_dict import AvailableRoutes

from pkg.service.user_storage import UserStorage


# TODO: put to middleware
def get_type(call: telegram_types.CallbackQuery):
    return json.loads(call.data).get("tp", "")


def message_route_validator(state_types: list[str], message: telegram_types.Message):
    if message.text is not None and message.text[0] == '/':
        return False

    return user_state(message) in state_types


def user_state(entity: telegram_types.Message | telegram_types.CallbackQuery):
    try:
        chat_id = entity.message.chat.id
    except AttributeError:
        chat_id = entity.chat.id
    return UserStorage.curr_state(chat_id)


def construct_params(
        call: telegram_types.CallbackQuery,
        message: telegram_types.Message,
        route_name: AvailableRoutes,
        action_name: str | None = None,
        is_step_back: bool = False
) -> ControllerParams:

    return {
        'call': call,
        'message': message,
        'route_name': route_name,
        'state_data': state_data.get_state_data(call, message, route_name, action_name),
        'is_step_back': is_step_back,

        'go_back_action': state_navigator.go_back,

        'language_code': call.from_user.language_code if call is not None else message.from_user.language_code,
    }


async def event_wrapper(
        route_name: AvailableRoutes, entity: telegram_types.Message | telegram_types.CallbackQuery,
        *args, **kwargs):
    # Args: manual
    # Kwargs: bot, event_from_user, ...

    call, message = call_and_message_accessed_processor(entity)

    # Validate access
    validator = RouteMap.get_route_prop(route_name, 'validator')
    if validator is not None:
        valid = await validator(call, message)
        if not valid:
            return

    menu_route: AvailableRoutes = 'menu'

    if call is None:
        # Clear state on commands
        if message_tools.is_command(message.text):
            UserStorage.new_navigation_journey(message.chat.id, menu_route)
        # Set resend on message
        UserStorage.set_resend(message.chat.id)

    method = RouteMap.get_route_prop(route_name, 'method')
    succeed = await method(construct_params(call, message, route_name))

    if succeed is not False:  # returns None by default
        UserStorage.change_page(message.chat.id, route_name)


async def event_action_wrapper(
        route_name: AvailableRoutes, action_name: str, call: telegram_types.CallbackQuery, *args, **kwargs):
    call, message = call_and_message_accessed_processor(call)

    params = construct_params(call, message, route_name, action_name)

    await RouteMap.get_route_action_prop(route_name, action_name, 'method')(params)
