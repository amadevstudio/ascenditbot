import json
from abc import ABC, abstractmethod
from typing import Callable, NoReturn, Literal

from project import constants
from project.types import ErrorDictInterface


class CallableInterface(ErrorDictInterface, total=False):
    amount: int


class PaymentProcessor(ABC):
    def __init__(
            self, credentials: dict, port: int, callback: Callable[[CallableInterface], NoReturn]):
        self.credentials = credentials
        self.port = port
        self.callback = callback

    # Validate package belongs to service
    @abstractmethod
    def validate_package(self, package: dict) -> bool: pass

    # Ensure sign validity, notify user
    @staticmethod
    def process_package(self, package: dict): pass

    @abstractmethod
    def generate_payment_link(
            self, amount: int, user_id: int, currency: str,
            culture: str = constants.default_currency, test: bool = False) -> str: pass


class PaymentServer:
    def __init__(self, port: int, payment_processors: list[PaymentProcessor]):
        self.port = port
        self.payment_processors = payment_processors

        self.start_server()

    def start_server(self):
        # TODO
        pass

    def incoming_package(self, package: str):
        decoded_package = self.decode_package(package)
        for payment_processor in self.payment_processors:
            if payment_processor.validate_package(decoded_package):
                payment_processor.process_package(decoded_package)
                break

    @staticmethod
    def decode_package(package: str) -> dict:
        return json.loads(package)
