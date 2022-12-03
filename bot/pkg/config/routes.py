from typing import Any

from pkg.controller import welcome_controller, chats_controller


class RouteMap:
    ROUTES = {
        "start": {
            "method": welcome_controller.start,
            "routes": [
                "menu"
            ],
            "commands": ["start"]
        },
        "menu": {
            "method": welcome_controller.menu,
            "routes": [
                "add_chat"
            ],
            "commands": ["menu"]
        },
        "add_chat": {
            "method": chats_controller.add_chat,
            "commands": ["add_chat"],
            "wait_for_input": True,
            # "available_from": ["call", "command", "message"],
            # "chat_type": types.ChatType.PRIVATE
        },
        "my_chats": {
            "method": chats_controller.my_chats,
            "commands": ["my_chats"],
            "wait_for_input": True
        },
        'chat': {
            'method': chats_controller.show,
            'actions': {
                'switch_active': {
                    'method': chats_controller.switch_active
                }
            }
        },

        "nowhere": {}
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
        if route is None or "commands" not in route:
            return ["menu"]

        return route["commands"]

    @staticmethod
    def get_route_main_command(route_name: str):
        return RouteMap.get_route_commands(route_name)[0]

    @staticmethod
    def type(route_type: str):
        if route_type not in RouteMap.ROUTES:
            return "menu"

        return route_type

    @staticmethod
    def state(route_state: str):
        return RouteMap.type(route_state)

    @staticmethod
    def action_type(route_state: str, action: str):
        actions = RouteMap.get_route_prop(route_state, 'actions')
        if actions is None:
            return None

        if action not in list(actions.keys()):
            return None

        return action
