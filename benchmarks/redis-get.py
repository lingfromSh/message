import asyncio
import cProfile

from redis.asyncio import StrictRedis

connection = StrictRedis(password="communication-2023")


async def get_data(id):
    for _ in range(amount):
        await connection.get(f"exid:{id}:endpoint")


amount = 10000
repeat_time = 5


async def benchmark():
    with cProfile.Profile() as pr:
        await asyncio.gather(*[get_data(i) for i in range(repeat_time)])
        pr.print_stats()


asyncio.run(benchmark())
