from typing import Any, TypedDict, Callable, List, Dict, Literal

from pkg.controller.user_controllers import allowed_users_controller, chats_controller, welcome_controller, \
    subscription_controller
from pkg.controller.user_controllers.validators.chat_access_validator import chat_access_validator

AvailableCommands = Literal['start', 'menu', 'add_chat', 'my_chats', 'subscription']
AvailableRoutes = Literal[
    'start', 'menu', 'add_chat', 'my_chats', 'chat',
    'add_to_chat_whitelist', 'chat_whitelist', 'allowed_user',
    'subscription', 'tariffs', 'fund', 'fund_amount',
    'nowhere']


class RouteActionsInterface(TypedDict):
    method: Callable


class RouteInterface(TypedDict, total=False):
    method: Callable
    routes: List[AvailableRoutes]
    commands: List[AvailableCommands]
    wait_for_input: bool
    actions: Dict[str, RouteActionsInterface]
    validator: Callable


class RoutesInterface(TypedDict):
    start: RouteInterface
    menu: RouteInterface
    add_chat: RouteInterface
    my_chats: RouteInterface
    chat: RouteInterface
    add_to_chat_whitelist: RouteInterface
    chat_whitelist: RouteInterface
    allowed_user: RouteInterface
    nowhere: RouteInterface


# TODO: use nesting routing
class RouteMap:
    ROUTES: RoutesInterface = {
        'start': {
            'method': welcome_controller.start,
            'commands': ['start'],
            'routes': [
                'menu'
            ],
        },
        'menu': {
            'method': welcome_controller.menu,
            'commands': ['menu'],
            'routes': [
                'add_chat',
                'my_chats',
                'subscription'
            ],
        },

        'add_chat': {
            'method': chats_controller.add_chat,
            'commands': ['add_chat'],
            'wait_for_input': True,
            # 'available_from': ['call', 'command', 'message'],
            # 'chat_type': types.ChatType.PRIVATE
        },

        'my_chats': {
            'method': chats_controller.my_chats,
            'commands': ['my_chats'],
            'routes': ['chat'],
            'wait_for_input': True,
        },
        'chat': {
            'method': chats_controller.show,
            'routes': [
                'add_to_chat_whitelist',
                'chat_whitelist'
            ],
            'actions': {
                'switch_active': {
                    'method': chats_controller.switch_active
                }
            },
            'validator': chat_access_validator
        },
        'add_to_chat_whitelist': {
            'method': allowed_users_controller.add_to_chat_whitelist,
            'wait_for_input': True,
            'validator': chat_access_validator
        },
        'chat_whitelist': {
            'method': allowed_users_controller.chat_whitelist,
            'routes': ['allowed_user'],
            'wait_for_input': True,
            'validator': chat_access_validator
        },
        'allowed_user': {
            'method': allowed_users_controller.show,
            'actions': {
                'switch_active': {
                    'method': allowed_users_controller.switch_active
                },
                'delete': {
                    'method': allowed_users_controller.delete
                }
            },
            'validator': chat_access_validator
        },
        'subscription': {
            'method': subscription_controller.page,
            'commands': ['subscription'],
            'routes': [
                'tariffs',
                'fund'
            ]
        },
        'tariffs': {
            'method': subscription_controller.tariffs,
            'actions': {
                'change_tariff': {
                    'method': subscription_controller.change_tariff
                }
            }
        },
        'fund': {
            'method': subscription_controller.fund_balance_page,
            'wait_for_input': True
        },
        'fund_amount': {
            'method': subscription_controller.fund_link_page,
            'wait_for_input': True
        },

        'nowhere': {}
    }

    @staticmethod
    def main_route():
        return list(RouteMap.ROUTES.keys())[0]

    @staticmethod
    def find_route(route: str, routes=None):
        if routes is None:
            routes = RouteMap.ROUTES

        for key in routes:
            if key == route:
                return routes[key]

        return None

    @staticmethod
    def get_route_prop(route_name: str, key: str = None) -> Any:
        route = RouteMap.find_route(route_name)
        if route is None:
            return None

        if key is None:
            return None

        return route.get(key, None)

    @staticmethod
    def get_route_action_prop(route_name: str, action_name: str, key: str = None):
        actions: dict = RouteMap.get_route_prop(route_name, 'actions')
        if actions is None:
            return None

        if key is None or action_name not in list(actions.keys()) or key not in actions[action_name]:
            return None

        return actions[action_name][key]

    @staticmethod
    def get_route_commands(route_name: str):
        route = RouteMap.find_route(route_name)
        if route is None or 'commands' not in route:
            return ['menu']

        return route['commands']

    @staticmethod
    def get_route_main_command(route_name: str):
        return RouteMap.get_route_commands(route_name)[0]

    # Get action type
    @staticmethod
    def type(route_type: str):
        if route_type not in RouteMap.ROUTES:
            return 'menu'

        return route_type

    # Get state from state list
    @staticmethod
    def state(route_state: str):
        return RouteMap.type(route_state)

    # Get inline action type
    @staticmethod
    def action_type(route_state: str, action: str):
        actions = RouteMap.get_route_prop(route_state, 'actions')
        if actions is None:
            return None

        if action not in list(actions.keys()):
            return None

        return action
