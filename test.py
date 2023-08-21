import asyncio

from aio_pika import connect_robust
from aio_pika.message import Message
from aio_pika.pool import Pool


async def connect():
    return await connect_robust(login="communication", password="communication-2023")


async def get_connection():
    return await connect()


pool = Pool(get_connection, max_size=10)


async def main():
    for i in range(100000):
        # async with pool.acquire() as connection:
        connection = await get_connection()
        channel = await connection.channel()
        exchange = await channel.get_exchange("message.topic.exchange")
        await exchange.publish(Message(body=b"test-connection"), routing_key="eventbus")


asyncio.run(main())
