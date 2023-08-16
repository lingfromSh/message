from redis.asyncio import Sentinel
from redis.asyncio.retry import Retry
from redis.backoff import ExponentialBackoff  # 指数退避
from redis.exceptions import BusyLoadingError
from redis.exceptions import ConnectionError
from sanic.log import logger

from common.depend import Dependency


class CacheDependency(Dependency, dependency_name="Cache", dependency_alias="cache"):
    async def prepare(self) -> bool:
        cache_config = self.app.config.CACHE
        sentinel_password_kwargs = {"password": cache_config.SENTINEL_PASSWORD}
        master_password_kwargs = {"password": cache_config.MASTER_PASSWORD}
        retry_kwargs = {
            "retry": Retry(ExponentialBackoff(), 3),
            "retry_on_timeout": True,
            "retry_on_error": [BusyLoadingError, ConnectionError],
        }
        print(sentinel_password_kwargs)
        self._sentinel = Sentinel(
            sentinels=[(cache_config.SENTINEL_HOST, cache_config.SENTINEL_PORT)],
            sentinel_kwargs={**sentinel_password_kwargs, **retry_kwargs},
            **{
                "health_check_interval": 1,
                **master_password_kwargs,
                **retry_kwargs,
            },
        )
        self._prepared = self._sentinel.master_for(cache_config.MASTER_SET)

        try:
            await self.get("HEALTH_CHECK")
            self.is_prepared = True
            logger.info("dependency:Cache is prepared")
        except Exception as err:
            logger.warn(f"dependency:Cache is not prepared, {str(err)}")
        finally:
            return self.is_prepared

    async def check(self) -> bool:
        if not self.is_prepared:
            await self.prepare()
            return self.is_prepared
        return True
