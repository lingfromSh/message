# Third Party Library
import orjson

# First Library
from infra.abc import CheckResult
from infra.abc import HealthStatus
from infra.abc import Infrastructure


class DistributionInfrastructure(Infrastructure):
    async def init(self, cache):
        self.cache = cache
        self.pubsubs = []
        return self

    async def shutdown(self, resource: Infrastructure):
        try:
            for pubsub in self.pubsubs:
                await pubsub.close()
        except Exception:
            pass

    async def health_check(self) -> HealthStatus:
        return HealthStatus(status="up")

    async def publish(self, channel, data):
        try:
            await self.cache.redis.publish(channel, orjson.dumps(data))
        except Exception as e:
            print(e)

    async def subscribe(self, channel):
        pubsub = self.cache.redis.pubsub()
        await pubsub.subscribe(channel)
        self.pubsubs.append(pubsub)
        return pubsub.listen()
