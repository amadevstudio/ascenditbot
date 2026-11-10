from typing import Any, TypedDict, Callable, Dict, Literal

from pkg.config.routes_dict import AvailableCommands, AvailableRoutes
from pkg.controller.admin_controllers import admin_controller, channels_controller, sources_controller
from pkg.controller.user_controllers import allowed_users_controller, chats_controller, welcome_controller, \
    subscription_controller, settings_controller, access_controller, post_limit_controller, channel_bonus_controller, \
    topics_controller
from pkg.controller.user_controllers.validators.admin_validator import admin_validator
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
    chat_restriction_duration: RouteInterface
    chat_access: RouteInterface
    chat_post_limit: RouteInterface
    chat_topics: RouteInterface
    allowed_user: RouteInterface
    subscription: RouteInterface
    tariffs: RouteInterface
    fund: RouteInterface
    fund_currency: RouteInterface
    fund_amount: RouteInterface
    settings: RouteInterface
    settings_email: RouteInterface
    settings_currency: RouteInterface
    bonus: RouteInterface
    admin: RouteInterface
    admin_bot: RouteInterface
    admin_sources: RouteInterface
    admin_source: RouteInterface
    admin_add_source: RouteInterface
    admin_channels: RouteInterface
    admin_add_channel: RouteInterface
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
        'privacy': {
            'method': welcome_controller.privacy,
            'available_from': ['command'],
        },
        'menu': {
            'method': welcome_controller.menu,
            'available_from': ['command', 'call'],
            'routes': [
                'add_chat',
                'my_chats',
                'help',
                'subscription',
                'settings',
                'bonus',
                'admin'
            ],
        },
        'bonus': {
            'method': channel_bonus_controller.page,
            'available_from': ['command', 'call'],
            'actions': {
                'bonus_check': {'method': channel_bonus_controller.check},
            },
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
                'chat_whitelist',
                'chat_restriction_duration',
                'chat_access',
                'chat_post_limit',
                'chat_topics'
            ],
            'actions': {
                'switch_active': {
                    'method': chats_controller.switch_active
                },
                'delete': {
                    'method': chats_controller.delete
                },
                'switch': {
                    'method': chats_controller.switch
                },
                'switch_mode': {
                    'method': chats_controller.switch_mode
                },
                'switch_admins': {
                    'method': chats_controller.switch_admins
                }
            },
            'validator': chat_access_validator
        },
        'add_to_chat_whitelist': {
            'method': allowed_users_controller.add_to_chat_whitelist,
            'available_from': ['message', 'call'],
            'wait_for_input': True,
            'validator': chat_access_validator,
            'have_under_keyboard': True
        },
        'chat_whitelist': {
            'method': allowed_users_controller.chat_whitelist,
            'available_from': ['message', 'call'],
            'routes': ['allowed_user', 'add_to_chat_whitelist'],
            'wait_for_input': True,
            'actions': {
                'wl_clean': {'method': allowed_users_controller.clean_ended},
            },
            'validator': chat_access_validator
        },
        'chat_restriction_duration': {
            'method': chats_controller.restriction_duration,
            'available_from': ['message', 'call'],
            'wait_for_input': True,
            'validator': chat_access_validator
        },
        'chat_post_limit': {
            'method': post_limit_controller.page,
            'available_from': ['message', 'call'],
            'wait_for_input': True,
            'actions': {
                'lim_set': {'method': post_limit_controller.set_limit},
            },
            'validator': chat_access_validator
        },
        'chat_topics': {
            'method': topics_controller.page,
            'available_from': ['call'],
            'actions': {
                'tpc_set': {'method': topics_controller.toggle},
                'tpc_def': {'method': topics_controller.toggle_default},
                'tpc_page': {'method': topics_controller.turn_page},
            },
            'validator': chat_access_validator
        },
        'chat_access': {
            'method': access_controller.page,
            'available_from': ['message', 'call'],
            'wait_for_input': True,
            'actions': {
                'acc_mode': {'method': access_controller.set_mode},
                'acc_edit': {'method': access_controller.edit},
                'acc_cancel': {'method': access_controller.cancel},
                'acc_post': {'method': access_controller.post},
                'acc_post_go': {'method': access_controller.post_go},
                'acc_requests': {'method': access_controller.requests},
                'acc_declined': {'method': access_controller.declined},
                'acc_map': {'method': access_controller.map_product},
            },
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
                },
                'set_term': {
                    'method': allowed_users_controller.set_term
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
            'routes': ['fund_currency'],
            'wait_for_input': True,
            'validator': email_presence_validator
        },
        'fund_currency': {
            'method': subscription_controller.fund_currency_page,
            'available_from': ['call'],
            'routes': ['fund_amount'],
            'wait_for_input': True,
            'validator': email_presence_validator
        },
        'fund_amount': {
            'method': subscription_controller.fund_link_page,
            'available_from': ['message', 'call'],
            'wait_for_input': True,
            'states_for_input': ['fund_currency', 'fund_amount'],
            'validator': email_presence_validator
        },

        'settings': {
            'method': settings_controller.page,
            'available_from': ['command', 'call'],
            'routes': ['settings_email', 'settings_currency']
        },
        'settings_email': {
            'method': settings_controller.email,
            'available_from': ['message', 'call'],
            'wait_for_input': True
        },
        'settings_currency': {
            'method': settings_controller.currency,
            'available_from': ['call'],
            'actions': {
                'change_currency': {
                    'method': settings_controller.change_currency
                }
            }
        },

        # The bot's owners only (users.is_admin): "🛠 Админка" in the menu, no commands
        'admin': {
            'method': admin_controller.menu,
            'available_from': ['call'],
            'routes': ['admin_bot', 'admin_sources', 'admin_channels'],
            'validator': admin_validator
        },
        'admin_bot': {
            'method': admin_controller.page,
            'available_from': ['call'],
            'validator': admin_validator
        },
        'admin_sources': {
            'method': sources_controller.list_page,
            'available_from': ['call'],
            'routes': ['admin_source', 'admin_add_source'],
            'validator': admin_validator
        },
        'admin_source': {
            'method': sources_controller.source_page,
            'available_from': ['call'],
            'actions': {
                'admin_delete_source': {'method': sources_controller.delete_source},
            },
            'validator': admin_validator
        },
        'admin_add_source': {
            'method': sources_controller.add_source,
            'available_from': ['message', 'call'],
            'wait_for_input': True,
            'validator': admin_validator
        },
        'admin_channels': {
            'method': channels_controller.page,
            'available_from': ['call'],
            'routes': ['admin_add_channel'],
            'actions': {
                'admin_delete_channel': {'method': channels_controller.delete_channel},
            },
            'validator': admin_validator
        },
        'admin_add_channel': {
            'method': channels_controller.add_channel,
            'available_from': ['message', 'call'],
            'wait_for_input': True,
            'validator': admin_validator
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
        all_child_routes = []

        curr_route = RouteMap.find_route(route_name)
        child_routes_stack = [*curr_route.get('routes', [])]

        while len(child_routes_stack) > 0:
            curr_route_name = child_routes_stack.pop()
            curr_route = RouteMap.find_route(curr_route_name)
            if curr_route is None:
                continue

            child_routes_stack.extend(curr_route.get('routes', []))

            all_child_routes.append(curr_route_name)

        return all_child_routes
