from typing import List
from typing import Optional

import orjson
from bson.objectid import ObjectId
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import EmailStr
from pydantic import Field
from pydantic import computed_field
from pydantic import model_validator

from apps.endpoint.models import Endpoint
from utils import get_app

from .types import ObjectID

app = get_app()


class CreateEndpointInputModel(BaseModel):
    external_id: str
    tags: Optional[List[str]]

    websockets: Optional[List[str]]
    emails: Optional[List[EmailStr]]


class QueryEndpointInputModel(BaseModel):
    external_ids: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    websockets: Optional[List[str]] = None
    emails: Optional[List[str]] = None
    page_size: Optional[int] = app.config.API.DEFAULT_PAGE_SIZE
    page: Optional[int] = app.config.API.DEFAULT_PAGE


class UpdateEndpointInputModel(BaseModel):
    external_id: str
    tags: Optional[List[str]] = None

    websockets: Optional[List[str]] = None
    emails: Optional[List[EmailStr]] = None


class DestroyEndpointInputModel(BaseModel):
    oids: Optional[List[ObjectID]]
    external_ids: Optional[List[str]]

    @model_validator(mode="after")
    def ensure_at_least_one(self):
        assert self.oids or self.external_ids, "ensure at least one is set"
        return self

    async def delete(self):
        conditions = []

        if self.oids:
            conditions.append({"_id": {"$in": list(map(ObjectId, self.oids))}})

        if self.external_ids:
            conditions.append({"external_id": {"$in": self.external_ids}})

        result = await Endpoint.collection.delete_many({"$or": conditions})
        return result.deleted_count


class EndpointOutputModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: ObjectID = Field(alias="pk")
    external_id: str
    tags: Optional[List[str]]

    websockets: Optional[List[str]]
    emails: Optional[List[EmailStr]]


class ETag:
    def __init__(self, v: str) -> None:
        self.v = v

    def __str__(self) -> str:
        return f"#etag:{self.v}"

    __repr__ = __str__

    async def decode(self):
        endpoints = []
        async for endpoint in Endpoint.find({"tags": self.v}):
            endpoints.append(endpoint)
        return endpoints


class ExID:
    def __init__(self, v: str) -> None:
        self.v = v

    def __str__(self) -> str:
        return f"#exid:{self.v}"

    __repr__ = __str__

    async def decode(self):
        try:
            cache = app.ctx.infra.cache()
            raw = await cache.get(f"exid:{self.v}:endpoint")
            if raw:
                data = orjson.loads(raw)
                return data
            return None
        except Exception as err:
            return None
