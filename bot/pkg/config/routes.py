from typing import Any, TypedDict, Callable, Dict, Literal

from pkg.config.routes_dict import AvailableCommands, AvailableRoutes
from pkg.controller.user_controllers import allowed_users_controller, chats_controller, welcome_controller, \
    subscription_controller, settings_controller
from pkg.controller.user_controllers.validators.chat_access_validator import chat_access_validator
from pkg.controller.user_controllers.validators.user_validator import email_presence_validator


class RouteActionsInterface(TypedDict):
    method: Callable


class RouteInterface(TypedDict, total=False):
    method: Callable
    available_from: list[Literal['command', 'message', 'call']]  # Which types of action trigger the route
    commands: list[AvailableCommands]  # Commands that triggers the route
    routes: list[AvailableRoutes]  # Routes that can be reached directly
    wait_for_input: bool
    states_for_input: list[AvailableRoutes]  # States for message input (for example, its own name)
    actions: Dict[str, RouteActionsInterface]
    validator: Callable
    have_under_keyboard: bool | None


class RoutesInterface(TypedDict):
    start: RouteInterface
    menu: RouteInterface
    add_chat: RouteInterface
    my_chats: RouteInterface
    chat: RouteInterface
    add_to_chat_whitelist: RouteInterface
    chat_whitelist: RouteInterface
    allowed_user: RouteInterface
    subscription: RouteInterface
    tariffs: RouteInterface
    fund: RouteInterface
    fund_amount: RouteInterface
    settings: RouteInterface
    settings_email: RouteInterface
    nowhere: RouteInterface


# TODO: use nesting routing
class RouteMap:
    ROUTES: dict[AvailableRoutes, RouteInterface] = {
        'start': {
            'method': welcome_controller.start,
            'available_from': ['command'],
            'routes': [
                'menu'
            ],
        },
        'menu': {
            'method': welcome_controller.menu,
            'available_from': ['command', 'call'],
            'routes': [
                'add_chat',
                'my_chats',
                'help',
                'subscription',
                'settings'
            ],
        },
        'help': {
            'method': welcome_controller.help_page,
            'available_from': ['command', 'call'],
        },

        'add_chat': {
            'method': chats_controller.add_chat,
            'available_from': ['command', 'message', 'call'],
            'wait_for_input': True,
            'have_under_keyboard': True
        },
        'my_chats': {
            'method': chats_controller.my_chats,
            'available_from': ['command', 'message', 'call'],
            'routes': ['chat'],
            'wait_for_input': True,
        },
        'chat': {
            'method': chats_controller.show,
            'available_from': ['call'],
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
            'available_from': ['message', 'call'],
            'wait_for_input': True,
            'validator': chat_access_validator
        },
        'chat_whitelist': {
            'method': allowed_users_controller.chat_whitelist,
            'available_from': ['message', 'call'],
            'routes': ['allowed_user'],
            'wait_for_input': True,
            'validator': chat_access_validator
        },
        'allowed_user': {
            'method': allowed_users_controller.show,
            'available_from': ['call'],
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
            'available_from': ['command', 'call'],
            'routes': [
                'tariffs',
                'fund'
            ]
        },
        'tariffs': {
            'method': subscription_controller.tariffs,
            'available_from': ['call'],
            'actions': {
                'change_tariff': {
                    'method': subscription_controller.change_tariff
                }
            }
        },
        'fund': {
            'method': subscription_controller.fund_balance_page,
            'available_from': ['call'],
            'wait_for_input': True,
            'validator': email_presence_validator
        },
        'fund_amount': {
            'method': subscription_controller.fund_link_page,
            'available_from': ['message', 'call'],
            'wait_for_input': True,
            'states_for_input': ['fund', 'fund_amount'],
            'validator': email_presence_validator
        },

        'settings': {
            'method': settings_controller.page,
            'available_from': ['command', 'call'],
            'routes': ['settings_email']
        },
        'settings_email': {
            'method': settings_controller.email,
            'available_from': ['message', 'call'],
            'wait_for_input': True
        },

        'nowhere': {}
    }

    @staticmethod
    def main_route():
        return list(RouteMap.ROUTES.keys())[0]

    # Returns route description
    @staticmethod
    def find_route(route_name: AvailableRoutes, routes=None) -> RouteInterface | None:
        if routes is None:
            routes = RouteMap.ROUTES

        for key in routes:
            if key == route_name:
                return routes[key]

        return None

    # Get route property
    @staticmethod
    def get_route_prop(route_name: AvailableRoutes, key: str) -> Any:
        route = RouteMap.find_route(route_name)
        if route is None:
            raise ValueError('Route not found')

        return route.get(key, None)

    # Get property of route's action
    @staticmethod
    def get_route_action_prop(route_name: AvailableRoutes, action_name: str, key: str) -> Any:
        actions: dict = RouteMap.get_route_prop(route_name, 'actions')
        if actions is None:
            return None

        if key is None or action_name not in list(actions.keys()) or key not in actions[action_name]:
            return None

        return actions[action_name][key]


    # Get route commands
    @staticmethod
    def get_route_commands(route_name: AvailableRoutes):
        route = RouteMap.find_route(route_name)
        if route is None or 'commands' not in route:
            return ['menu']

        return route['commands']

    # Get first route command
    @staticmethod
    def get_route_main_command(route_name: AvailableRoutes):
        return RouteMap.get_route_commands(route_name)[0]

    # Get action type (or base)
    @staticmethod
    def type(route_type: AvailableRoutes) -> AvailableRoutes:
        if route_type not in RouteMap.ROUTES:
            return 'menu'

        return route_type

    # Get inline action type
    @staticmethod
    def action_type(route_state: AvailableRoutes, action: str):
        actions = RouteMap.get_route_prop(route_state, 'actions')
        if actions is None:
            return None

        if action not in list(actions.keys()):
            return None

        return action

    @staticmethod
    def child_routes(route_name: AvailableRoutes) -> list[AvailableRoutes] | None:
        child_routes = []
        child_routes_stack = [*RouteMap.get_route_prop(route_name, 'routes')]

        while len(child_routes_stack) > 0:
            curr_route_name = child_routes_stack.pop()
            curr_route = RouteMap.find_route(curr_route_name)
            if curr_route is None:
                continue

            child_routes_stack.extend(curr_route.get('routes', []))

            child_routes.append(curr_route_name)

        return child_routes
