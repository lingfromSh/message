import asyncio

from aio_pika import connect_robust
from aio_pika.pool import Pool
from sanic.log import logger

from common.depend import Dependency


def connection_pool_factory(app):
    connection_kwargs = {
        "host": app.config.QUEUE.HOST,
        "port": app.config.QUEUE.PORT,
        "login": app.config.QUEUE.USERNAME,
        "password": app.config.QUEUE.PASSWORD,
    }

    async def connection_factory():
        return await connect_robust(**connection_kwargs, timeout=1)

    return connection_factory


class QueueDependency(Dependency, dependency_name="Queue", dependency_alias="queue"):
    MAX_CHANNEL_NUM = 8092

    def __init__(self, app):
        self.channel_counter = 0
        super().__init__(app)

    async def prepare(self) -> bool:
        self.is_prepared = False

        try:
            self._prepared = Pool(connection_pool_factory(self.app), max_size=4)
            self.is_prepared = True
        except asyncio.TimeoutError:
            self._prepared = None
        if self.is_prepared:
            logger.info("dependency:Queue is prepared")
        return self.is_prepared

    async def check(self) -> bool:
        if not self.is_prepared:
            await self.prepare()

        return self.is_prepared
