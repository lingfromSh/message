import logging

from aio_pika import connect_robust
from aio_pika.pool import Pool
from aiormq.exceptions import ConnectionNotAllowed
from retry import retry

logger = logging.getLogger()

logger.setLevel(logging.DEBUG)


async def make_connection():
    return await connect_robust(
        "amqp://communication:communication-2023@localhost:5672/",
    )


async def make_channel(connection_pool):
    async with connection_pool.acquire() as connection:
        return await connection.channel()


async def main():
    connection_pool = Pool(make_connection, max_size=100)
    channel_pool = Pool(make_channel, connection_pool, max_size=8092)
    for i in range(100000):
        manager = channel_pool.acquire()
        c = await manager.pool._get()
        print(c)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
