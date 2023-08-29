from typing import Any
from redis.asyncio import Sentinel
from redis.asyncio.retry import Retry
from redis.backoff import ExponentialBackoff  # 指数退避
from redis.exceptions import BusyLoadingError
from redis.exceptions import ConnectionError
from sanic.log import logger


class CacheDependency:
    def __init__(
        self,
        sentinel_host,
        sentinel_port,
        sentinel_password,
        master_set,
        master_password,
    ):
        self.retry_kwargs = {
            "retry": Retry(ExponentialBackoff(), 3),
            "retry_on_timeout": True,
            "retry_on_error": [BusyLoadingError, ConnectionError],
        }
        self.sentinel_password_kwargs = {"password": sentinel_password}
        self.master_password_kwargs = {"password": master_password}

        self.sentinel = Sentinel(
            [(sentinel_host, sentinel_port)],
            sentinel_kwargs={**self.sentinel_password_kwargs, **self.retry_kwargs},
            **{
                "health_check_interval": 1,
                **self.master_password_kwargs,
                **self.retry_kwargs,
            },
        )
        self.master = self.sentinel.master_for(master_set)
        logger.info("dependency: cache is configured")

    def __getattribute__(self, name: str) -> Any:
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            return object.__getattribute__(self.master, name)
