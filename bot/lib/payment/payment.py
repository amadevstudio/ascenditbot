import asyncio
from abc import ABC, abstractmethod
from typing import Callable, NoReturn, TypedDict, Awaitable
from aiohttp import web

from lib.python.logger import Logger


class ErrorDictInterface(TypedDict, total=False):
    error: str


class CallableInterface(ErrorDictInterface, total=False):
    amount: int
    currency: str
    user_id: int
    service: str


class PaymentProcessor(ABC):
    AVAILABLE_CURRENCIES = []

    def __init__(
            self, credentials: dict, incoming_payment_callback: Callable[[CallableInterface], Awaitable[NoReturn]],
            logger: Logger = None):
        self.credentials = credentials
        self.incoming_payment_callback = incoming_payment_callback

        self.logger = logger
        # TODO: logger initiation

    def log(self, *args):
        if self.logger is not None:
            self.logger.warning(str(self.__class__), *args)
        else:
            print(str(self.__class__), *args, flush=True)

    # Validate package belongs to service
    @abstractmethod
    def validate_package(self, package: dict, service: str) -> bool: pass

    # Ensure sign validity, notify user
    @abstractmethod
    async def process_package(self, package_params: dict) -> str: pass

    @abstractmethod
    def generate_payment_link(
            self, amount: float, user_id: int, currency: str, culture: str, test: bool = False
    ) -> str | ErrorDictInterface: pass


class PaymentServer:
    def __init__(self, port: int, payment_processors: list[PaymentProcessor]):
        self.port = port
        self.payment_processors = payment_processors

        loop = asyncio.get_event_loop()
        loop.create_task(self.start_server())

    async def handle(self, request: web.BaseRequest):
        service = request.match_info.get('service', "")
        answer_text = await self.incoming_package(request, service)
        if answer_text is not None:
            return web.Response(text=answer_text)

    async def start_server(self):
        app = web.Application()
        app.add_routes([web.get('/payment/{service}/result', self.handle)])
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', self.port)
        await site.start()

    async def incoming_package(self, package: web.BaseRequest, service: str) -> str | None:
        decoded_package_params = self.decode_package(package)
        for payment_processor in self.payment_processors:
            if payment_processor.validate_package(decoded_package_params, service):
                return await payment_processor.process_package(decoded_package_params)

        return None

    @staticmethod
    def decode_package(package: web.BaseRequest) -> dict:
        return dict(package.rel_url.query)
