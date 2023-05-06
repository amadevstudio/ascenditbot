from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery

from framework.controller.router_tools import message_route_validator, user_state, get_type

from pkg.config.routes import RouteMap
from pkg.config.routes_dict import AvailableRoutes


class CurrentStateMessageFilter(BaseFilter):
    def __init__(self, routes: list[AvailableRoutes]):
        self.routes = routes

    async def __call__(self, message: Message) -> bool:
        return message_route_validator(self.routes, message)


class CurrentStateActionFilter(BaseFilter):
    def __init__(self, route: AvailableRoutes, action: str):
        self.route = route
        self.action = action

    async def __call__(self, call: CallbackQuery) -> bool:
        return (
            user_state(call) == self.route
            and get_type(call) == RouteMap.action_type(self.route, self.action))
