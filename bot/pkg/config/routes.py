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
            "commands": ["add_chat"]
            # "available_from": ["call", "command", "message"],
            # "chat_type": types.ChatType.PRIVATE
        },
        "my_chats": {
            "method": chats_controller.my_chats,
            "commands": ["my_chats"]
        },

        "nowhere": {}
    }

    @staticmethod
    def find_route(route: str, routes=None):
        if routes is None:
            routes = RouteMap.ROUTES

        for key in routes:
            if key == route:
                return routes[key]

        return None

    @staticmethod
    def get_route(route_name: str, key: str = None):
        route = RouteMap.find_route(route_name)
        if route is None:
            return None

        if key is not None:
            return route.get(key, None)

        return None

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
        return RouteMap.get_route_main_command(route_type)

    @staticmethod
    def state(route_state: str):
        return RouteMap.get_route_main_command(route_state)
