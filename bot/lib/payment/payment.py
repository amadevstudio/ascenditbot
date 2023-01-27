import asyncio
import concurrent
import json
from abc import ABC, abstractmethod
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Callable, NoReturn, Literal, TypedDict
from aiohttp import web


class ErrorDictInterface(TypedDict, total=False):
    error: str


class CallableInterface(ErrorDictInterface, total=False):
    amount: int


class PaymentProcessor(ABC):
    AVAILABLE_CURRENCIES = []

    def __init__(
            self, credentials: dict, callback: Callable[[CallableInterface], NoReturn]):
        self.credentials = credentials
        self.callback = callback

    # Validate package belongs to service
    @abstractmethod
    def validate_package(self, package: dict) -> bool: pass

    # Ensure sign validity, notify user
    @staticmethod
    def process_package(self, package: dict): pass

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
        name = request.match_info.get('name', "Anonymous")
        text = "Hello, " + name
        print('Request served!')
        return web.Response(text=text)

    async def start_server(self):
        app = web.Application()
        app.add_routes([web.get('/', self.handle),
                        web.get('/{name}', self.handle)])
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', self.port)
        await site.start()

    def incoming_package(self, package: str):
        decoded_package = self.decode_package(package)
        for payment_processor in self.payment_processors:
            if payment_processor.validate_package(decoded_package):
                payment_processor.process_package(decoded_package)
                break

    @staticmethod
    def decode_package(package: str) -> dict:
        return json.loads(package)
