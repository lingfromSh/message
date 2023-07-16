from common.depend import Dependency
from redis.asyncio import Sentinel
from redis.backoff import ExponentialBackoff  # 指数退避
from redis.exceptions import BusyLoadingError, ConnectionError
from redis.asyncio.retry import Retry


class CacheDependency(Dependency, dependency_name="Cache", dependency_alias="cache"):
    async def prepare(self) -> bool:
        self.is_prepared = True
        cache_config = self.app.config.CACHE
        sentinel_password_kwargs = {"password": cache_config.SENTINEL_PASSWORD}
        master_password_kwargs = {"password": cache_config.MASTER_PASSWORD}
        retry_kwargs = {
            "retry": Retry(ExponentialBackoff(), 3),
            "retry_on_timeout": True,
            "retry_on_error": [BusyLoadingError, ConnectionError],
        }
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
            await self._prepared.get("HEALTH_CHECK")
            self.is_prepared = True
        except Exception:
            pass
        finally:
            return self.is_prepared

    async def check(self) -> bool:
        if not self.is_prepared:
            await self.prepare()
            return self.is_prepared
        return True
