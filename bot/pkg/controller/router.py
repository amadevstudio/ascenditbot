from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import Update

from framework.controller.router_tools import get_type, user_state, event_wrapper, event_action_wrapper
from framework.controller import state_navigator
from pkg.config.routes import RouteMap
from pkg.controller.middlewares import NoWhereInputProcessorMiddleware
from pkg.controller.routers.user_router import user_router
from pkg.controller.routers.work_router import work_router


def init_routes(environment):
    bot = Bot(token=environment['TELEGRAM_BOT_TOKEN'])
    dispatcher = Dispatcher(bot)

    dispatcher.middleware.setup(NoWhereInputProcessorMiddleware())

    # !!!
    # Functional routes
    @dispatcher.callback_query_handler(lambda call: get_type(call) == 'back')
    async def go_back(call: types.Message | types.CallbackQuery):
        await state_navigator.go_back(call)

    # !!!
    # Logical routes

    # for route in RouteMap.ROUTES:
    #     route_params = RouteMap.ROUTES[route]
    #     if {'command', 'call', 'message'} == set(route_params['available_from']):
    #         @dispatcher.message_handler(commands=[route], chat_type=route_params.get('chat_type', True))
    #         @dispatcher.message_handler(
    #             lambda message: get_curr_state() == route, chat_type=route_params.get('chat_type', True))
    #         @dispatcher.callback_query_handler(
    #             lambda call: get_type(call) == route, chat_type=route_params.get('chat_type', True))
    #         async def function(entity: types.Message | types.CallbackQuery):
    #             call, message = call_and_message_accessed_processor(entity)
    #             await RouteMap.get_route(route, 'method')(call, message)
    #     elif 'command' in route_params['available_from'] and 'call' in route_params['available_from']:
    #         @dispatcher.message_handler(commands=[route], chat_type=route_params.get('chat_type', True))
    #         @dispatcher.callback_query_handler(
    #             lambda call: get_type(call) == route, chat_type=route_params.get('chat_type', True))
    #         async def function(entity: types.Message | types.CallbackQuery):
    #             call, message = call_and_message_accessed_processor(entity)
    #             await RouteMap.get_route(route, 'method')(call, message)
    #     elif 'command' in route_params['available_from']:
    #         @dispatcher.message_handler(commands=[route], chat_type=route_params.get('chat_type', True))
    #         async def function(entity: types.Message | types.CallbackQuery):
    #             call, message = call_and_message_accessed_processor(entity)
    #             await RouteMap.get_route(route, 'method')(call, message)
    #     elif 'call' in route_params['available_from']:
    #         @dispatcher.callback_query_handler(
    #             lambda call: get_type(call) == route, chat_type=route_params.get('chat_type', True))
    #         async def function(entity: types.Message | types.CallbackQuery):
    #             call, message = call_and_message_accessed_processor(entity)
    #             await RouteMap.get_route(route, 'method')(call, message)

    user_router(dispatcher)

    work_router(dispatcher)

    return executor, dispatcher
