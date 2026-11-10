import os
import sys
from typing import TypedDict

run_from_path = os.path.abspath(sys.argv[0])
if os.path.isfile(run_from_path):
    BASE_DIR = os.path.dirname(run_from_path)
else:
    BASE_DIR = run_from_path
LOGS_FOLDER = os.path.join(BASE_DIR, 'logs')


class EnvironmentInterface(TypedDict):
    ENVIRONMENT: str

    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_ADMIN_GROUP_ID: str

    REDIS_PASSWORD: str

    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    ROBOKASSA_LOGIN: str
    ROBOKASSA_PAYMENT_P1: str
    ROBOKASSA_PAYMENT_P2: str
    ROBOKASSA_PAYMENT_P1_TEST: str
    ROBOKASSA_PAYMENT_P2_TEST: str

    # Optional (my.telegram.org): MTProto for topics by id; without them topics are learned from messages only
    TELEGRAM_API_ID: str | None
    TELEGRAM_API_HASH: str | None


environment: EnvironmentInterface = {
    'ENVIRONMENT': os.environ['ENVIRONMENT'],

    'TELEGRAM_BOT_TOKEN': os.environ['TELEGRAM_BOT_TOKEN'],
    'TELEGRAM_ADMIN_GROUP_ID': os.environ['TELEGRAM_ADMIN_GROUP_ID'],

    'REDIS_PASSWORD': os.environ['REDIS_PASSWORD'],

    'POSTGRES_DB': os.environ['POSTGRES_DB'],
    'POSTGRES_USER': os.environ['POSTGRES_USER'],
    'POSTGRES_PASSWORD': os.environ['POSTGRES_PASSWORD'],

    'ROBOKASSA_LOGIN': os.environ['ROBOKASSA_LOGIN'],
    'ROBOKASSA_PAYMENT_P1': os.environ['ROBOKASSA_PAYMENT_P1'],
    'ROBOKASSA_PAYMENT_P2': os.environ['ROBOKASSA_PAYMENT_P2'],
    'ROBOKASSA_PAYMENT_P1_TEST': os.environ['ROBOKASSA_PAYMENT_P1_TEST'],
    'ROBOKASSA_PAYMENT_P2_TEST': os.environ['ROBOKASSA_PAYMENT_P2_TEST'],

    'TELEGRAM_API_ID': os.environ.get('TELEGRAM_API_ID') or None,
    'TELEGRAM_API_HASH': os.environ.get('TELEGRAM_API_HASH') or None,
}

empty_photo_link = "https://cdn3.iconfinder.com/data/icons/online-states/150/Photos-512.png"
