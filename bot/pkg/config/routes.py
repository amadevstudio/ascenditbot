import enum

from pkg.controller import welcome_controller


class RouteMap:

    ROUTES = {
        "start": {
            "method": welcome_controller.start,
            "routes": [
                "menu"
            ],
        },
        "menu": {
            "method": welcome_controller.menu,
            "routes": [
            ],
        }
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
