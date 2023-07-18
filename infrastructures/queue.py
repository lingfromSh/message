import asyncio
import async_timeout
from contextlib import suppress
from sanic.log import logger
from common.depend import Dependency
from aio_pika import connect, Connection
from aio_pika.connection import make_url


class QueueDependency(Dependency, dependency_name="Queue", dependency_alias="queue"):
    async def prepare(self) -> bool:
        self.is_prepared = False

        connection_kwargs = {
            "host": self.app.config.QUEUE.HOST,
            "port": self.app.config.QUEUE.PORT,
            "login": self.app.config.QUEUE.USERNAME,
            "password": self.app.config.QUEUE.PASSWORD,
        }

        try:
            self._prepared = await connect(**connection_kwargs, timeout=1)
            self.is_prepared = True
        except asyncio.TimeoutError:
            self._prepared = Connection(make_url(**connection_kwargs))
        if self.is_prepared:
            logger.info("dependency: Queue is prepared")

    async def check(self) -> bool:
        if self.is_prepared:
            try:
                async with async_timeout.timeout(1):
                    channel = await self._prepared.channel()
                    await channel.close()
            except BaseException:
                self.is_prepared = False
                with suppress(asyncio.TimeoutError):
                    async with async_timeout.timeout(1):
                        await self._prepared.reconnect()
        else:
            try:
                await self._prepared.connect(timeout=1)
            except BaseException:
                pass

        self.is_prepared = self._prepared.connected.is_set()
        return self.is_prepared
