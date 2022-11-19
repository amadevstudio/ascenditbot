import sys

from aiogram import Bot, Dispatcher, executor, types

from pkg.controller import welcome_controller


def init_routes(environment):
    bot = Bot(token=environment["TELEGRAM_BOT_TOKEN"])
    dispatcher = Dispatcher(bot)

    @dispatcher.message_handler(chat_type=types.ChatType.PRIVATE, commands=['start'])
    async def start(message: types.Message):
        await welcome_controller.start(message)

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
