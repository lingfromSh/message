from typing import Any

import environ
from sanic.config import Config as SanicConfig

from .api import APIConfig
from .cache import CacheConfig
from .database import DatabaseConfig
from .queue import QueueConfig


@environ.config(prefix="MESSAGE")
class Config:
    API = environ.group(APIConfig)
    CACHE = environ.group(CacheConfig)
    DATABASE = environ.group(DatabaseConfig)
    QUEUE = environ.group(QueueConfig)

    WEBSOCKET_PING_INTERVAL = environ.var(default=30, converter=int)
    WEBSOCKET_PING_TIMEOUT = environ.var(default=30, converter=int)


config = environ.to_config(Config)


class ConfigProxy(SanicConfig):
    def __getattr__(self, attr: Any):
        try:
            return getattr(config, attr)
        except AttributeError:
            pass
        try:
            return self[attr]
        except KeyError as ke:
            raise AttributeError(f"Config has no '{ke.args[0]}'")
