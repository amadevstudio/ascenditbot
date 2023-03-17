from framework.system import telegram_types

from pkg.config import routes
from pkg.service.user_storage import UserStorage

from pkg.config.routes import RouteMap


async def go_back(call: telegram_types.CallbackQuery):
    if call.message:
        # try:
        # lastText = storage.get_user_last_text(call.message.chat.id)
        prev, curr = UserStorage.prev_curr_states(call.message.chat.id)

        method = RouteMap.get_route_prop(prev, 'method')
        if method is None:
            # TODO: show error
            return

        await method(call, call.message, change_user_state=False)

        if curr is None:
            curr = routes.RouteMap.main_route()

        UserStorage.go_back(call.message.chat.id, curr)

        # except Exception as e:
        #     welcome_controller.menu(call.message)


# If status is 'nowhere' and previous waits for text goback to previously and process
def nowhere_input_processor(message: telegram_types.Message):
    prev, curr = UserStorage.prev_curr_states(message.chat.id)
    if curr is None:
        curr = routes.RouteMap.main_route()

    if prev is not None and RouteMap.get_route_prop(prev, "wait_for_input") and RouteMap.state("nowhere") == curr:
        UserStorage.go_back(message.chat.id)
