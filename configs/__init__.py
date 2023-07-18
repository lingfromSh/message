from typing import Any

import environ
from sanic.config import Config as SanicConfig

from .cache import CacheConfig


@environ.config(prefix="MESSAGE")
class Config:
    CACHE = environ.group(CacheConfig)

    WEBSOCKET_PING_INTERVAL = environ.var(
        default=600, name="WEBSOCKET_PING_INTERVAL", converter=int
    )
    WEBSOCKET_PING_TIMEOUT = environ.var(
        default=600, name="WEBSOCKET_PING_TIMEOUT", converter=int
    )


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
