import asyncio
import cProfile
import pstats
from typing import List
from typing import Optional

import ulid

MONGODB_HOST = "localhost"
MONGODB_PORT = 27017
MONGODB_USER = "communication"
MONGODB_PASSWORD = "communication-2023"

# umongo
from motor.motor_asyncio import AsyncIOMotorClient

client = AsyncIOMotorClient(
    f"mongodb://{MONGODB_USER}:{MONGODB_PASSWORD}@{MONGODB_HOST}:{MONGODB_PORT}",
    maxConnecting=100,
)

uid = str(ulid.ULID())


async def test_umongo_insert(amount):
    from umongo import Document
    from umongo import fields
    from umongo.frameworks.motor_asyncio import MotorAsyncIOInstance

    instance = MotorAsyncIOInstance(client.message)

    @instance.register
    class Endpoint(Document):
        external_id = fields.StringField()
        tags = fields.ListField(fields.StringField())
        websockets = fields.ListField(fields.StringField())
        emails = fields.ListField(fields.StringField())

    for i in range(amount):
        endpoint = Endpoint(external_id=uid, tags=["admin"], websockets=[uid])
        await endpoint.commit()


async def test_umongo_query(amount):
    from umongo import Document
    from umongo import fields
    from umongo.frameworks.motor_asyncio import MotorAsyncIOInstance

    instance = MotorAsyncIOInstance(client.message)

    @instance.register
    class Endpoint(Document):
        external_id = fields.StringField()
        tags = fields.ListField(fields.StringField())
        websockets = fields.ListField(fields.StringField())
        emails = fields.ListField(fields.StringField())

    async for endpoint in Endpoint.find().limit(amount):
        endpoint


from beanie import Document as BeanieDocument
from beanie import init_beanie


async def test_beanie_insert(amount):
    class Endpoint(BeanieDocument):
        external_id: str
        tags: Optional[List[str]] = None
        websockets: Optional[List[str]] = None
        emails: Optional[List[str]] = None

    await init_beanie(client.message, document_models=[Endpoint])
    for i in range(amount):
        endpoint = Endpoint(external_id=uid, tags=["admin"], websockets=[uid])
        await endpoint.insert()


async def test_beanie_query(amount):
    class Endpoint(BeanieDocument):
        external_id: str
        tags: Optional[List[str]] = None
        websockets: Optional[List[str]] = None
        emails: Optional[List[str]] = None

    await init_beanie(client.message, document_models=[Endpoint])

    async for endpoint in Endpoint.find(limit=amount):
        endpoint


amount = 10000
repeat_time = 5


async def asyncio_benchmark():
    with cProfile.Profile() as pr:
        await asyncio.gather(*[test_umongo_insert(amount) for i in range(repeat_time)])
        pr.dump_stats(f"umongo-insert-{amount}")

    with cProfile.Profile() as pr:
        await asyncio.gather(*[test_beanie_insert(amount) for i in range(repeat_time)])
        pr.dump_stats(f"beanie-insert-{amount}")

    stats = pstats.Stats()
    stats.add(f"umongo-insert-{amount}")
    stats.sort_stats("tottime").print_stats()

    stats = pstats.Stats()
    stats.add(f"beanie-insert-{amount}")
    stats.sort_stats("tottime").print_stats()

    with cProfile.Profile() as pr:
        await asyncio.gather(*[test_umongo_query(amount) for i in range(repeat_time)])
        pr.dump_stats(f"umongo-query-{amount}")

    with cProfile.Profile() as pr:
        await asyncio.gather(*[test_beanie_query(amount) for i in range(repeat_time)])
        pr.dump_stats(f"beanie-query-{amount}")

    stats = pstats.Stats()
    stats.add(f"umongo-query-{amount}")
    stats.sort_stats("tottime").print_stats()

    stats = pstats.Stats()
    stats.add(f"beanie-query-{amount}")
    stats.sort_stats("tottime").print_stats()


def test_mongoengine_insert(amount):
    from mongoengine import Document
    from mongoengine import connect
    from mongoengine import fields

    connect("message", username="communication", password="communication-2023")

    class Endpoint(Document):
        external_id = fields.StringField()
        tags = fields.ListField(fields.StringField())
        websockets = fields.ListField(fields.StringField())
        emails = fields.ListField(fields.StringField())

    for i in range(amount):
        endpoint = Endpoint(external_id=uid, tags=["admin"], websockets=[uid])
        endpoint.save()


def test_mongoengine_query(amount):
    from mongoengine import Document
    from mongoengine import connect
    from mongoengine import fields

    connect("message", username="communication", password="communication-2023")

    class Endpoint(Document):
        external_id = fields.StringField()
        tags = fields.ListField(fields.StringField())
        websockets = fields.ListField(fields.StringField())
        emails = fields.ListField(fields.StringField())

    for endpoint in Endpoint.objects:
        endpoint


def sync_benchmark():
    for i in range(repeat_time):
        with cProfile.Profile() as pr:
            test_mongoengine_insert(amount)
            pr.dump_stats(f"mongoengine-{i+1}-insert-{amount}")

    stats = pstats.Stats()
    stats.add(*[f"mongoengine-{i+1}-insert-{amount}" for i in range(repeat_time)])
    stats.sort_stats("tottime").print_stats()

    for i in range(repeat_time):
        with cProfile.Profile() as pr:
            test_mongoengine_query(amount)
            pr.dump_stats(f"mongoengine-{i+1}-query-{amount}")

    stats = pstats.Stats()
    stats.add(*[f"mongoengine-{i+1}-query-{amount}" for i in range(repeat_time)])
    stats.sort_stats("tottime").print_stats()


asyncio.run(asyncio_benchmark())
