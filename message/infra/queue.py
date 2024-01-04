# Third Party Library
from aio_pika import connect_robust
from aio_pika.pool import Pool
from aio_pika.robust_channel import RobustChannel
from aio_pika.robust_connection import RobustConnection
from message.infra.abc import CheckResult
from message.infra.abc import HealthStatus
from message.infra.abc import Infrastructure


async def connection_factory(url):
    return await connect_robust(url)


async def channel_factory(connection_pool: Pool[RobustConnection]):
    async with connection_pool.acquire() as connection:
        return await connection.channel()


class QueueInfrastructure(Infrastructure):
    async def init(self, url: str) -> Infrastructure:
        self.connection_pool: Pool[RobustConnection] = Pool(
            connection_factory,
            url,
            max_size=4,
        )
        self.channel_pool: Pool[RobustChannel] = Pool(
            channel_factory,
            self.connection_pool,
            max_size=1000,
        )
        return self

    async def shutdown(self, resource: Infrastructure):
        try:
            await self.channel_pool.close()
            await self.connection_pool.close()
        except Exception:
            pass

    async def health_check(self) -> HealthStatus:
        return await super().health_check()
