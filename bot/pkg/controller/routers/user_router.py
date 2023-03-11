from functools import partial

import aiogram
from aiogram import types, Router, F
from aiogram.filters.command import Command

from framework.controller import state_navigator
from framework.controller.router_tools import event_wrapper, event_action_wrapper
from framework.controller.filters.chat_type import ChatTypeFilter

from pkg.config.routes import RouteMap, AvailableRoutes
from pkg.controller.middlewares import NoWhereInputProcessorMiddleware
from pkg.controller.filters.current_state import CurrentStateMessageFilter, CurrentStateActionFilter
from pkg.controller.filters.callback_button_type import CallbackButtonTypeFilter, BackButtonHandler

PRIVATE_CHAT = aiogram.enums.chat_type.ChatType.PRIVATE


def user_router():
    router = Router()

    router.message.middleware(NoWhereInputProcessorMiddleware())

    # @dp.message(Command("test1"))
    # async def cmd_test1(message: types.Message):
    #     await message.reply("Test 1")
    #
    # dp.message.register(cmd_test2, Command("test2"))

    @router.callback_query(ChatTypeFilter(PRIVATE_CHAT), BackButtonHandler())
    async def go_back(call: types.CallbackQuery):
        await state_navigator.go_back(call)

    route: AvailableRoutes
    for route in RouteMap.ROUTES:
        if route == 'nowhere':
            continue

        route_params = RouteMap.ROUTES[route]
        handler = partial(event_wrapper, RouteMap.type(route))

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
                action_handler = partial(
                    event_action_wrapper, RouteMap.type(route), RouteMap.action_type(route, action))
                router.callback_query.register(
                    action_handler, ChatTypeFilter(PRIVATE_CHAT),
                    CurrentStateActionFilter(route, action))

    return router
