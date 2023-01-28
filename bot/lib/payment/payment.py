import asyncio
import concurrent
import json
from abc import ABC, abstractmethod
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Callable, NoReturn, Literal, TypedDict
from aiohttp import web

from lib.python.logger import Logger


class ErrorDictInterface(TypedDict, total=False):
    error: str


class CallableInterface(ErrorDictInterface, total=False):
    amount: int


class PaymentProcessor(ABC):
    AVAILABLE_CURRENCIES = []

    def __init__(
            self, credentials: dict, incoming_payment_callback: Callable[[CallableInterface], NoReturn],
            logger: Logger = None):
        self.credentials = credentials
        self.incoming_payment_callback = incoming_payment_callback

        # self.logger = logger if logger is not None else Logger()
        # TODO: logger initiation

    # Validate package belongs to service
    @abstractmethod
    def validate_package(self, package: dict) -> bool: pass

    # Ensure sign validity, notify user
    def process_package(self, package: dict) -> str: pass

    @abstractmethod
    def generate_payment_link(
            self, amount: float, user_id: int, currency: str, culture: str) -> str | ErrorDictInterface: pass


class PaymentServer:
    def __init__(self, port: int, payment_processors: list[PaymentProcessor]):
        self.port = port
        self.payment_processors = payment_processors

        loop = asyncio.get_event_loop()
        loop.create_task(self.start_server())

    async def handle(self, request):
        # result_url = request.match_info.get('result', "fail")
        result_text = self.incoming_package(request)
        if result_text is not None:
            return web.Response(text=result_text)

    async def start_server(self):
        app = web.Application()
        app.add_routes([web.get('/payment/{result}', self.handle)])
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', self.port)
        await site.start()

    def incoming_package(self, package: str) -> str | None:
        decoded_package = self.decode_package(package)
        for payment_processor in self.payment_processors:
            if payment_processor.validate_package(decoded_package):
                return payment_processor.process_package(decoded_package)

        return None

    @staticmethod
    def decode_package(package: str) -> dict:
        return json.loads(package)
