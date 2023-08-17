from typing import Any

import environ
from sanic.config import Config as SanicConfig

from .api import APIConfig
from .cache import CacheConfig
from .database import DatabaseConfig
from .queue import QueueConfig
from sanic.log import logger


@environ.config(prefix="MESSAGE")
class Config:
    API = environ.group(APIConfig)
    CACHE = environ.group(CacheConfig)
    DATABASE = environ.group(DatabaseConfig)
    QUEUE = environ.group(QueueConfig)

    WEBSOCKET_PING_INTERVAL = environ.var(default=5, converter=int)
    WEBSOCKET_PING_TIMEOUT = environ.var(default=5, converter=int)


config = environ.to_config(Config)

print("==== Server Env Config ====")
print("[API Env Config]")
print(config.API)
print("[CACHE Env Config]")
print(config.CACHE)
print("[DATABASE Env Config]")
print(config.DATABASE)
print("[QUEUE Env Config]")
print(config.QUEUE)


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
