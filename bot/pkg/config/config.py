import os
from typing import TypedDict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class EnvironmentInterface(TypedDict):
    TELEGRAM_BOT_TOKEN: str
    REDIS_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    ROBOKASSA_LOGIN: str
    ROBOKASSA_PAYMENT_P1: str
    ROBOKASSA_PAYMENT_P2: str


environment: EnvironmentInterface = {
    'TELEGRAM_BOT_TOKEN': os.environ['TELEGRAM_BOT_TOKEN'],

    'REDIS_PASSWORD': os.environ['REDIS_PASSWORD'],

    'POSTGRES_DB': os.environ['POSTGRES_DB'],
    'POSTGRES_USER': os.environ['POSTGRES_USER'],
    'POSTGRES_PASSWORD': os.environ['POSTGRES_PASSWORD'],

    'ROBOKASSA_LOGIN': os.environ['ROBOKASSA_LOGIN'],
    'ROBOKASSA_PAYMENT_P1': os.environ['ROBOKASSA_PAYMENT_P1'],
    'ROBOKASSA_PAYMENT_P2': os.environ['ROBOKASSA_PAYMENT_P2']
}

empty_photo_link = "https://cdn3.iconfinder.com/data/icons/online-states/150/Photos-512.png"
