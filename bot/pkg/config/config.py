import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

environment = {
    "TELEGRAM_BOT_TOKEN": os.environ['TELEGRAM_BOT_TOKEN'],
    "REDIS_PASSWORD": os.environ['REDIS_PASSWORD'],
    "POSTGRES_DB": os.environ['POSTGRES_DB'],
    "POSTGRES_USER": os.environ['POSTGRES_USER'],
    "POSTGRES_PASSWORD": os.environ['POSTGRES_PASSWORD'],
}

empty_photo_link = "https://cdn3.iconfinder.com/data/icons/online-states/150/Photos-512.png"
