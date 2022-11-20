import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

environment = {
    "TELEGRAM_BOT_TOKEN": os.environ['TELEGRAM_BOT_TOKEN'],
    "REDIS_PASSWORD": os.environ['REDIS_PASSWORD']
}
