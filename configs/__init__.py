from typing import Any

import environ
from sanic.config import Config as SanicConfig

from .cache import CacheConfig


@environ.config(prefix="MESSAGE")
class Config:
    CACHE = environ.group(CacheConfig)


config = environ.to_config(Config)


class ConfigProxy(SanicConfig):
    def __getattr__(self, attr: Any):
        try:
            return self[attr]
        except KeyError:
            pass
        try:
            return getattr(config, attr)
        except AttributeError as ae:
            raise AttributeError(f"Config has no '{ae.args[0]}'")
