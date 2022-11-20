from pkg.service import user_storage

from pkg.config.routes import RouteMap


async def go_back(call):
    if call.message:
        # try:
        # lastText = storage.get_user_last_text(call.message.chat.id)
        prev, curr = user_storage.prev_curr_states(call.message.chat.id)

        method = RouteMap.get_method(prev)
        if method is None:
            # TODO: show error
            return

        await method(call, change_user_state=False)

        user_storage.go_back(call.message.chat.id)

        # except Exception as e:
        #     welcome_controller.menu(call.message)

