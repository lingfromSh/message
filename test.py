import asyncio
from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorClient
from umongo import Document
from umongo import fields
from umongo.frameworks.motor_asyncio import MotorAsyncIOInstance

client = AsyncIOMotorClient(
    "mongodb://communication:communication-2023@localhost:27017"
)
instance = MotorAsyncIOInstance(db=client.message)


@instance.register
class Provider(Document):
    type = fields.StringField(required=True, max_length=32)
    code = fields.StringField(required=True)
    name = fields.StringField(required=True, unique=True)
    config = fields.DictField(required=False, allow_none=True)

    created_at = fields.AwareDateTimeField(required=True)
    updated_at = fields.AwareDateTimeField(required=True)

    class Meta:
        collection_name = "providers"


@instance.register
class Message(Document):
    provier = fields.ReferenceField("Provider", required=True)
    realm = fields.DictField(required=True)
    status = fields.StringField(required=True)

    created_at = fields.AwareDateTimeField(required=True)
    updated_at = fields.AwareDateTimeField(required=True)

    class Meta:
        collection_name = "messages"


async def main():
    from umongo.fields import ObjectId

    ps = []
    for i in range(400000, 1000000):
        p = Provider(
            type="websocket",
            name=f"websocket{i}",
            code="websocket",
            config=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        ps.append(p.to_mongo())
    await client.message.providers.insert_many(ps)


asyncio.run(main())
