from pkg.service import user_storage

from pkg.config.routes import RouteMap
from pkg.system.logger import logger


async def go_back(call):
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

