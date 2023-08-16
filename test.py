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


@instance.register
class Endpoint(Document):
    external_id = fields.StringField(required=True, unique=True)
    tags = fields.ListField(fields.StringField(), required=False, allow_none=True)
    websockets = fields.ListField(fields.StringField(), required=False, allow_none=True)
    emails = fields.ListField(fields.EmailField(), required=False, allow_none=True)

    class Meta:
        collection_name = "endpoints"


async def main():
    from umongo.fields import ObjectId

    ps = []
    for i in range(20000000, 30000000):
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


# asyncio.run(main())

from typing import Annotated
from typing import List
from typing import Union

from asgiref.sync import async_to_sync
from pydantic import BaseModel
from pydantic import PlainValidator
from pydantic import field_serializer


def validate_etag(v: str):
    assert v.startswith("#etg:")
    return ETag(v[5:])


def validate_exid(v: str):
    assert v.startswith("#exid:")
    return EExID(v[6:])


class ETag:
    def __init__(self, v) -> None:
        self.v = v

    def __str__(self) -> str:
        return f"<ETag: '{self.v}'>"

    __repr__ = __str__

    def serialize(self):
        async def get_endpoints():
            endpoints = []
            async for endpoint in Endpoint.find({"tag": self.v}):
                endpoints.append(endpoint)
            return endpoints

        return async_to_sync(get_endpoints)()


class EExID:
    def __init__(self, v) -> None:
        self.v = v

    def __str__(self) -> str:
        return f"<EExID: '{self.v}'>"

    __repr__ = __str__

    def serialize(self):
        async def get_endpoint():
            try:
                await Endpoint.find_one({"external_id": self.v})
            except Exception:
                return None

        return async_to_sync(get_endpoint)()


EndpointTag = Annotated[ETag, PlainValidator(validate_etag)]
EndpointExID = Annotated[EExID, PlainValidator(validate_exid)]


class Model(BaseModel):
    connections: List[Union[EndpointTag, EndpointExID, str]]

    @field_serializer("connections")
    def serialize_connections(self, connections, _info):
        ret = []

        for c in connections:
            if isinstance(c, EExID):
                ret.append(c.serialize())
            elif isinstance(c, ETag):
                ret.extend(c.serialize())
            else:
                ret.append(c)
        return list(filter(lambda x: x, ret))


async def main():
    async with await client.start_session() as session:
        async with session.start_transaction():
            endpoint = await Endpoint.find_one({"external_id": "studio:1"})
            endpoint.websockets = ["test"]
            await endpoint.commit()


asyncio.run(main())
