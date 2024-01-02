# Third Party Library
from redis.asyncio.client import StrictRedis

# First Library
from infra.abc import CheckResult
from infra.abc import HealthStatus
from infra.abc import Infrastructure


class CacheInfrastructure(Infrastructure):
    # TODO: add support for redis cluster, sentinel, etc.
    async def init(self, url: str):
        self.redis = StrictRedis.from_url(url)
        return self

    async def shutdown(self, resource: Infrastructure):
        await self.redis.aclose()

    async def health_check(self) -> HealthStatus:
        checks = []
        try:
            if await self.redis.ping():
                checks.append(
                    CheckResult(check="ping check", status="up", result="ping is ok")
                )
            else:
                checks.append(
                    CheckResult(
                        check="ping check",
                        status="down",
                        result="something went wrong",
                    )
                )
        except Exception as err:
            checks.append(
                CheckResult(check="ping check", status="down", result=str(err))
            )

        # summary all checks
        if all(map(lambda c: c.status == "up", checks)):
            status = "up"
        else:
            status = "down"

        return HealthStatus(
            status=status,
            checks=checks,
        )
