import redis

from lib.python.singleton import Singleton


class Storage(metaclass=Singleton):
    def __init__(self):
        self.connection = None

    def connect(self, config: dict[str, str] = None):
        if config is not None:
            # self.connection = redis.ConnectionPool(
            self.connection = redis.Redis(
                host=config['host'], port=config['port'], password=config['password'])
        else:
            self.connection = redis.Redis()
