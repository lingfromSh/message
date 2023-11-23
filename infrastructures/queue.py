from aio_pika import connect_robust
from aio_pika.abc import AbstractChannel
from aio_pika.abc import AbstractConnection
from aio_pika.pool import Pool
from sanic.log import logger


class QueueDependency:
    def __init__(
        self,
        host,
        port: int = 5672,
        username: str = "guest",
        password: str = None,
        virtual_host: str = "/",
        max_connection_size: int = 10,
        max_channel_size: int = 8092,
    ) -> None:
        async def make_connection() -> AbstractConnection:
            return await connect_robust(
                host=host,
                port=port,
                login=username,
                password=password,
                virtualhost=virtual_host,
                reconnect_interval=5,
            )

        async def make_channel() -> AbstractChannel:
            async with self.connection_pool.acquire() as connection:
                return await connection.channel()

        self.connection_pool: Pool[AbstractConnection] = Pool(
            make_connection, max_size=max_connection_size
        )
        self.channel_pool: Pool[AbstractChannel] = Pool(
            make_channel, max_size=max_channel_size
        )

        logger.debug("dependency: queue is configured")
