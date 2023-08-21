import cProfile, pstats
import asyncio
import orjson
from ulid import ULID
from pydantic import EmailStr
from pydantic import BaseModel
from typing import Optional, List
from redis.asyncio import StrictRedis


class Endpoint(BaseModel):
    external_id: str
    tags: Optional[List[str]] = None
    websockets: Optional[List[str]] = None
    emails: Optional[List[EmailStr]] = None


connection = StrictRedis(password="communication-2023")


async def test_redisom_insert(amount):
    for i in range(amount):
        await connection.set(
            str(ULID()),
            orjson.dumps({"external_id": str(ULID()), "websockets": [str(ULID())]}),
        )


amount = 10000
repeat_time = 5


async def asyncio_benchmark():
    with cProfile.Profile() as pr:
        await asyncio.gather(*[test_redisom_insert(amount) for i in range(repeat_time)])
        pr.print_stats()


asyncio.run(asyncio_benchmark())
