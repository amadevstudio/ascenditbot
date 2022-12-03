from aiogram import types

from pkg.service import user_storage

from pkg.config.routes import RouteMap
from pkg.system.logger import logger


async def go_back(call: types.CallbackQuery):
    if call.message:
        # try:
        # lastText = storage.get_user_last_text(call.message.chat.id)
        prev, curr = user_storage.prev_curr_states(call.message.chat.id)

        method = RouteMap.get_route(prev, "method")
        if method is None:
            # TODO: show error
            return

        await method(call, call.message, change_user_state=False)

        user_storage.go_back(call.message.chat.id)

        # except Exception as e:
        #     welcome_controller.menu(call.message)


# If status is 'nowhere' and previous waits for text goback to previously and process
def nowhere_input_processor(message: types.Message):
    prev, curr = user_storage.prev_curr_states(message.chat.id)
    if prev is not None and RouteMap.get_route(prev, "wait_for_input") and RouteMap.state("nowhere") == curr:
        user_storage.go_back(message.chat.id)
