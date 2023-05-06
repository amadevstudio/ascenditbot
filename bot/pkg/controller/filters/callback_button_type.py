from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery

from framework.controller.router_tools import get_type
from pkg.config.routes import RouteMap
from pkg.config.routes_dict import AvailableRoutes


class BackButtonHandler(BaseFilter):
    async def __call__(self, call: CallbackQuery):
        return get_type(call) == 'back'


class CallbackButtonTypeFilter(BaseFilter):
    def __init__(self, button_type: AvailableRoutes):
        self.button_type = button_type

    async def __call__(self, call: CallbackQuery) -> bool:
        return get_type(call) == RouteMap.type(self.button_type)
