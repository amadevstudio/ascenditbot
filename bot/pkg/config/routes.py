from pkg.controller import welcome_controller


class RouteMap:
    ROUTES = {
        "start": {
            "method": welcome_controller.start,
            "routes": [
                "menu"
            ],
            "with_image": True
        },
        "menu": {
            "method": welcome_controller.menu,
            "routes": [
            ],
            "with_image": False
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
    def get_method(route: str):
        route = RouteMap.find_route(route)
        if route is None:
            return None

        return route["method"]
