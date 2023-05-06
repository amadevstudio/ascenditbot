from framework.controller.router_tools import construct_params
from framework.system import telegram_types

from pkg.service.user_storage import UserStorage

from pkg.config.routes import RouteMap
from pkg.config.routes_dict import AvailableRoutes


async def go_back(call: telegram_types.CallbackQuery, custom_prev: AvailableRoutes = None):
    if call.message:
        # try:
        # lastText = storage.get_user_last_text(call.message.chat.id)
        prev, curr = UserStorage.prev_curr_states(call.message.chat.id)
        print(prev, curr, flush=True)
        active_prev = prev if custom_prev is None else custom_prev
        if active_prev is None:
            return

        method = RouteMap.get_route_prop(active_prev, 'method')
        if method is None:
            # TODO: show error
            return

        all_states = UserStorage.all_states(call.message.chat.id)
        for state in reversed(all_states):
            if state == prev:
                break
            UserStorage.go_back(call.message.chat.id)

        await method(construct_params(call, call.message, active_prev, is_step_back=True))

        for child_route in RouteMap.child_routes(active_prev):
            UserStorage.del_user_state_data(call.message.chat.id, child_route)

        # except Exception as e:
        #     welcome_controller.menu(call.message)


# If status is 'nowhere' and previous waits for text goback to previously and process
def nowhere_input_processor(message: telegram_types.Message):
    prev, curr = UserStorage.prev_curr_states(message.chat.id)

    nowhere: AvailableRoutes = 'nowhere'

    if prev is not None and RouteMap.get_route_prop(prev, "wait_for_input") and curr == nowhere:
        UserStorage.go_back(message.chat.id)
