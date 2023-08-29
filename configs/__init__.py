from typing import Any, Callable, Dict, Optional, Sequence, Union

import environ
from inspect import getmembers
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

    WEBSOCKET_PING_INTERVAL = environ.var(default=600, converter=int)
    WEBSOCKET_PING_TIMEOUT = environ.var(default=600, converter=int)


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


def convert_config_to_dict(c) -> Dict:
    ret = {}
    for name, value in getmembers(c, lambda x: not callable(x)):
        if not name.isupper():
            continue
        if isinstance(value, (str, int, list)):
            ret[name] = value
        else:
            ret[name] = convert_config_to_dict(value)
    return ret


class ConfigProxy(SanicConfig):
    def __init__(self):
        super().__init__()
        self.update_config(convert_config_to_dict(config))

    def __getattr__(self, attr: Any):
        try:
            return getattr(config, attr)
        except AttributeError:
            pass
        try:
            return self[attr]
        except KeyError as ke:
            raise AttributeError(f"Config has no '{ke.args[0]}'")
