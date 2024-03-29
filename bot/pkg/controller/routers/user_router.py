from functools import partial

import aiogram
from aiogram import Router, F
from aiogram.filters.command import Command

from framework.system import telegram_types
from framework.controller import state_navigator
from framework.controller.router_tools import event_wrapper, event_action_wrapper
from framework.controller.filters.chat_type import ChatTypeFilter

from pkg.config.routes import RouteMap
from pkg.config.routes_dict import AvailableRoutes
from pkg.controller.middlewares.middlewares import NoWhereInputProcessorMiddleware, ReplyMarkupCleaner
from pkg.controller.filters.current_state import CurrentStateMessageFilter, CurrentStateActionFilter
from pkg.controller.filters.callback_button_type import CallbackButtonTypeFilter, BackButtonHandler

PRIVATE_CHAT = aiogram.enums.chat_type.ChatType.PRIVATE


def user_router():
    router = Router()

    router.message.outer_middleware(NoWhereInputProcessorMiddleware())

    router.message.middleware(ReplyMarkupCleaner())
    router.callback_query.middleware(ReplyMarkupCleaner())

    @router.callback_query(ChatTypeFilter(PRIVATE_CHAT), BackButtonHandler())
    async def go_back(call: telegram_types.CallbackQuery):
        await state_navigator.go_back(call)

    @router.message(
        F.chat_shared, ChatTypeFilter(PRIVATE_CHAT),
        CurrentStateMessageFilter(['add_chat']))
    async def add_chat_result(message: telegram_types.Message):
        handler = partial(event_wrapper, 'add_chat')
        await handler(message)

    route: AvailableRoutes
    for route in RouteMap.ROUTES:
        if route == 'nowhere':
            continue

        route_params = RouteMap.ROUTES[route]
        handler = partial(event_wrapper, route)

        if 'command' in route_params['available_from']:
            router.message.register(
                handler, Command(route_params.get('commands', route)), F.text,
                ChatTypeFilter(PRIVATE_CHAT))
        if 'message' in route_params['available_from']:
            router.message.register(
                handler, F.text, ChatTypeFilter(PRIVATE_CHAT),
                CurrentStateMessageFilter(route_params.get('states_for_input', [route])))
        if 'call' in route_params['available_from']:
            router.callback_query.register(
                handler, ChatTypeFilter(PRIVATE_CHAT),
                CallbackButtonTypeFilter(route))

        if 'actions' in route_params:
            for action in route_params['actions']:
                action_handler = partial(event_action_wrapper, route, action)
                router.callback_query.register(
                    action_handler, ChatTypeFilter(PRIVATE_CHAT),
                    CurrentStateActionFilter(route, action))

    return router
