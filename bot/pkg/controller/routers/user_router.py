from aiogram import types

from framework.controller.router_tools import event_wrapper, get_type, user_state, event_action_wrapper
from pkg.config.routes import RouteMap


def user_router(dispatcher):
    @dispatcher.message_handler(commands=RouteMap.get_route_commands('start'), chat_type=types.ChatType.PRIVATE)
    async def start(entity: types.Message):
        await event_wrapper(RouteMap.type('start'), entity)

    @dispatcher.message_handler(commands=RouteMap.get_route_commands('menu'), chat_type=types.ChatType.PRIVATE)
    @dispatcher.callback_query_handler(
        lambda call: get_type(call) == RouteMap.type('menu'), chat_type=types.ChatType.PRIVATE)
    async def menu(entity: types.Message | types.CallbackQuery):
        await event_wrapper(RouteMap.type('menu'), entity)

    @dispatcher.message_handler(commands=RouteMap.get_route_commands('add_chat'), chat_type=types.ChatType.PRIVATE)
    @dispatcher.message_handler(
        lambda message: user_state(message) == RouteMap.state('add_chat'), content_types=types.ContentType.ANY,
        chat_type=types.ChatType.PRIVATE)
    @dispatcher.callback_query_handler(
        lambda call: get_type(call) == RouteMap.type('add_chat'), chat_type=types.ChatType.PRIVATE)
    async def add_group(entity: types.Message | types.CallbackQuery, *args, **kwargs):
        await event_wrapper(RouteMap.type('add_chat'), entity)

    @dispatcher.message_handler(commands=RouteMap.get_route_commands('my_chats'), chat_type=types.ChatType.PRIVATE)
    @dispatcher.message_handler(
        lambda message: user_state(message) == RouteMap.state('my_chats'), chat_type=types.ChatType.PRIVATE)
    @dispatcher.callback_query_handler(
        lambda call: get_type(call) == RouteMap.type('my_chats'), chat_type=types.ChatType.PRIVATE)
    async def my_chats(entity: types.Message | types.CallbackQuery, *args, **kwargs):
        await event_wrapper(RouteMap.type('my_chats'), entity)

    @dispatcher.callback_query_handler(
        lambda call: get_type(call) == RouteMap.type('chat'), chat_type=types.ChatType.PRIVATE)
    async def chat(call: types.CallbackQuery):
        await event_wrapper(RouteMap.type('chat'), call)

    @dispatcher.callback_query_handler(
        lambda call: (
                user_state(call) == RouteMap.state('chat')
                and get_type(call) == RouteMap.action_type('chat', 'switch_active')),
        chat_type=types.ChatType.PRIVATE)
    async def chat_switch_active(call: types.CallbackQuery):
        await event_action_wrapper(RouteMap.type('chat'), RouteMap.action_type('chat', 'switch_active'), call)

    @dispatcher.callback_query_handler(
        lambda call: get_type(call) == RouteMap.type('add_to_chat_whitelist'), chat_type=types.ChatType.PRIVATE)
    @dispatcher.message_handler(
        lambda message: user_state(message) == RouteMap.state('add_to_chat_whitelist'),
        chat_type=types.ChatType.PRIVATE)
    async def chat_switch_active(entity: types.Message | types.CallbackQuery):
        await event_wrapper(RouteMap.type('add_to_chat_whitelist'), entity)

    @dispatcher.callback_query_handler(
        lambda call: get_type(call) == RouteMap.type('chat_whitelist'), chat_type=types.ChatType.PRIVATE)
    @dispatcher.message_handler(
        lambda message: user_state(message) == RouteMap.state('chat_whitelist'), chat_type=types.ChatType.PRIVATE)
    async def chat_whitelist(entity: types.Message | types.CallbackQuery):
        await event_wrapper(RouteMap.type('chat_whitelist'), entity)

    @dispatcher.callback_query_handler(
        lambda call: get_type(call) == RouteMap.type('allowed_user'), chat_type=types.ChatType.PRIVATE)
    async def allowed_user(call: types.CallbackQuery):
        await event_wrapper(RouteMap.type('allowed_user'), call)

    @dispatcher.callback_query_handler(
        lambda call: (
                user_state(call) == RouteMap.state('allowed_user')
                and get_type(call) == RouteMap.action_type('allowed_user', 'switch_active')),
        chat_type=types.ChatType.PRIVATE)
    async def allowed_user_switch_active(call: types.CallbackQuery):
        await event_action_wrapper(
            RouteMap.type('allowed_user'), RouteMap.action_type('allowed_user', 'switch_active'), call)

    @dispatcher.callback_query_handler(
        lambda call: (
                user_state(call) == RouteMap.state('allowed_user')
                and get_type(call) == RouteMap.action_type('allowed_user', 'delete')),
        chat_type=types.ChatType.PRIVATE)
    async def allowed_user_switch_active(call: types.CallbackQuery):
        await event_action_wrapper(
            RouteMap.type('allowed_user'), RouteMap.action_type('allowed_user', 'delete'), call)

    @dispatcher.message_handler(commands=RouteMap.get_route_commands('subscription'), chat_type=types.ChatType.PRIVATE)
    @dispatcher.callback_query_handler(
        lambda call: get_type(call) == RouteMap.type('subscription'), chat_type=types.ChatType.PRIVATE)
    async def my_chats(entity: types.Message | types.CallbackQuery, *args, **kwargs):
        await event_wrapper(RouteMap.type('subscription'), entity)

    @dispatcher.callback_query_handler(
        lambda call: get_type(call) == RouteMap.type('tariffs'), chat_type=types.ChatType.PRIVATE)
    async def chat(call: types.CallbackQuery):
        await event_wrapper(RouteMap.type('tariffs'), call)