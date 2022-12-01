from aiogram import Bot, Dispatcher, executor, types

from framework.controller.router_tools import get_type, user_state, event_wrapper
from framework.controller import state_navigator
from pkg.config.routes import RouteMap


def init_routes(environment):
    bot = Bot(token=environment["TELEGRAM_BOT_TOKEN"])
    dispatcher = Dispatcher(bot)

    # for route in RouteMap.ROUTES:
    #     route_params = RouteMap.ROUTES[route]
    #     if {'command', 'call', 'message'} == set(route_params["available_from"]):
    #         @dispatcher.message_handler(commands=[route], chat_type=route_params.get('chat_type', True))
    #         @dispatcher.message_handler(
    #             lambda message: get_curr_state() == route, chat_type=route_params.get('chat_type', True))
    #         @dispatcher.callback_query_handler(
    #             lambda call: get_type(call) == route, chat_type=route_params.get('chat_type', True))
    #         async def function(entity: types.Message | types.CallbackQuery):
    #             call, message = call_and_message_accessed_processor(entity)
    #             await RouteMap.get_route(route, 'method')(call, message)
    #     elif "command" in route_params["available_from"] and "call" in route_params["available_from"]:
    #         @dispatcher.message_handler(commands=[route], chat_type=route_params.get('chat_type', True))
    #         @dispatcher.callback_query_handler(
    #             lambda call: get_type(call) == route, chat_type=route_params.get('chat_type', True))
    #         async def function(entity: types.Message | types.CallbackQuery):
    #             call, message = call_and_message_accessed_processor(entity)
    #             await RouteMap.get_route(route, 'method')(call, message)
    #     elif "command" in route_params["available_from"]:
    #         @dispatcher.message_handler(commands=[route], chat_type=route_params.get('chat_type', True))
    #         async def function(entity: types.Message | types.CallbackQuery):
    #             call, message = call_and_message_accessed_processor(entity)
    #             await RouteMap.get_route(route, 'method')(call, message)
    #     elif "call" in route_params["available_from"]:
    #         @dispatcher.callback_query_handler(
    #             lambda call: get_type(call) == route, chat_type=route_params.get('chat_type', True))
    #         async def function(entity: types.Message | types.CallbackQuery):
    #             call, message = call_and_message_accessed_processor(entity)
    #             await RouteMap.get_route(route, 'method')(call, message)

    @dispatcher.message_handler(commands=RouteMap.get_route_commands("start"), chat_type=types.ChatType.PRIVATE)
    async def start(entity: types.Message):
        await event_wrapper(RouteMap.type("start"), entity)

    @dispatcher.message_handler(commands=RouteMap.get_route_commands("menu"), chat_type=types.ChatType.PRIVATE)
    @dispatcher.callback_query_handler(
        lambda call: get_type(call) == RouteMap.type("menu"), chat_type=types.ChatType.PRIVATE)
    async def menu(entity: types.Message | types.CallbackQuery):
        await event_wrapper(RouteMap.type("menu"), entity)

    @dispatcher.message_handler(commands=RouteMap.get_route_commands("add_chat"), chat_type=types.ChatType.PRIVATE)
    @dispatcher.message_handler(
        lambda message: user_state(message) == RouteMap.state("add_chat"), content_types=types.ContentType.ANY,
        chat_type=types.ChatType.PRIVATE)
    @dispatcher.callback_query_handler(
        lambda call: get_type(call) == RouteMap.type("add_chat"), chat_type=types.ChatType.PRIVATE)
    async def add_group(entity: types.Message | types.CallbackQuery):
        await event_wrapper(RouteMap.type("add_chat"), entity)

    @dispatcher.message_handler(commands=RouteMap.get_route_commands("my_chats"), chat_type=types.ChatType.PRIVATE)
    @dispatcher.message_handler(
        lambda message: user_state(message) == RouteMap.state("my_chats"), chat_type=types.ChatType.PRIVATE)
    @dispatcher.callback_query_handler(
        lambda call: get_type(call) == RouteMap.type("my_chats"), chat_type=types.ChatType.PRIVATE)
    async def my_chats(entity: types.Message | types.CallbackQuery):
        await event_wrapper(RouteMap.type("my_chats"), entity)


    @dispatcher.callback_query_handler(lambda call: get_type(call) == 'back')
    async def go_back(call: types.Message | types.CallbackQuery):
        await state_navigator.go_back(call)

    return executor, dispatcher

    # @dp.message_handler(chat_type=types.ChatType.PRIVATE, commands=['add_user'])
    # @validator
    # async def add_user(message: types.Message):
    #     username = get_username_from_command(message).strip()
    #     if username == '':
    #         await message.reply("Имя пользователя не может быть пустым")
    #         return
    #
    #     database.add_user(username, 0)
    #     await message.reply(f"Пользователь '{username}' добавлен в белый список")
    #
    #
    # @dp.message_handler(chat_type=types.ChatType.PRIVATE, commands=['delete_user'])
    # @validator
    # async def delete_user(message: types.Message):
    #     username = get_username_from_command(message).strip()
    #     database.delete_user(username, 0)
    #     await message.reply(f"Пользователь '{username}' удалён из белого списка")
    #
    #
    # @dp.message_handler(chat_type=types.ChatType.PRIVATE, commands=['show_white_list'])
    # @validator
    # async def show_white_list(message: types.Message):
    #     white_list = database.get_white_list_users()
    #     if white_list.__len__() == 0:
    #         await message.reply('Пользователей нет')
    #     else:
    #         responce = ''
    #         for user in white_list:
    #             responce += user['username'] + '\n'
    #         await message.reply(responce)
    #
    #
    # @dp.message_handler(lambda message: message.chat.type != types.ChatType.PRIVATE, content_types=types.ContentType.ANY)
    # async def message_filter(message: types.Message):
    #     username = message.from_user.username
    #     able_to_write = database.is_able_to_write(username)
    #     if not able_to_write:
    #         await message.delete()
